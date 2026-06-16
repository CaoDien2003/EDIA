import os
import shutil
import tempfile
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Security, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel

from src.config import ADMIN_KEY, TOP_K
from src.embeddings.embedder import get_embedder
from src.ingest import ingest
from src.llm.qwen import QwenLLM
from src.vectorstores.chroma_store import ChromaStore

PROMPT_TEMPLATE = """Answer based only on the context below. If the answer is not in the context, say you don't know.

Context:
{context}

Question:
{question}"""

resources: dict = {}

_admin_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)


def require_admin(key: str = Security(_admin_key_header)) -> None:
    if key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")


@asynccontextmanager
async def lifespan(app: FastAPI):
    resources["store"] = ChromaStore(get_embedder())
    resources["llm"] = QwenLLM()
    yield
    resources.clear()


app = FastAPI(title="PDF AI Assistant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── User ──────────────────────────────────────────────────────

class Source(BaseModel):
    file: str
    page: int


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    store: ChromaStore = resources["store"]
    docs = store.similarity_search(req.question, k=TOP_K)
    if not docs:
        raise HTTPException(status_code=404, detail="No relevant documents found")

    context = "\n\n".join(d.page_content for d in docs)
    prompt = PROMPT_TEMPLATE.format(context=context, question=req.question)
    answer_text = resources["llm"].generate(prompt)

    sources = [
        Source(
            file=d.metadata.get("source", "unknown"),
            page=int(d.metadata.get("page", 0)),
        )
        for d in docs
    ]
    return ChatResponse(answer=answer_text, sources=sources)


# ── Admin ─────────────────────────────────────────────────────

class DocumentInfo(BaseModel):
    name: str
    uploaded_at: str


@app.get("/admin/documents", response_model=list[DocumentInfo], dependencies=[Depends(require_admin)])
def list_documents() -> list[DocumentInfo]:
    return [DocumentInfo(**d) for d in resources["store"].list_sources()]


@app.post("/admin/upload", dependencies=[Depends(require_admin)])
async def upload_document(file: UploadFile) -> dict:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        count = ingest(tmp_path, resources["store"], original_name=file.filename)
    finally:
        os.remove(tmp_path)

    return {"message": f"Indexed {count} chunks from {file.filename}"}


@app.delete("/admin/documents/{name}", dependencies=[Depends(require_admin)])
def delete_document(name: str) -> dict:
    count = resources["store"].delete_by_source(name)
    if count == 0:
        raise HTTPException(status_code=404, detail=f"Document '{name}' not found")
    return {"message": f"Deleted {count} chunks from {name}"}
