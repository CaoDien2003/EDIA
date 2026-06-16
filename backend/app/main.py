from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models import Document, Session, Message, Event, Webhook  # noqa: F401 — triggers ORM registration
from app.database import Base
from app.api.v1.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Load models once at startup so the first request is not penalised
    from app.core.embeddings import get_embedder
    from app.core.llm import get_llm
    from app.core.vectorstore import _store
    get_embedder()
    get_llm()
    _store()

    yield


app = FastAPI(
    title="Enterprise Document Intelligence Assistant",
    version="1.0.0",
    description="RAG-powered chatbot with conversation memory, webhooks, and n8n automation",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "version": "1.0.0"}
