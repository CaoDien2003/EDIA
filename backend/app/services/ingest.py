import tempfile
from datetime import date
from pathlib import Path

import fitz  # pymupdf
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.core.vectorstore import add_documents


def _load_pdf(path: str) -> list[Document]:
    docs = []
    with fitz.open(path) as pdf:
        for i, page in enumerate(pdf):
            text = page.get_text()
            if text.strip():
                docs.append(Document(page_content=text, metadata={"page": i + 1}))
    return docs


def _chunk(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    return splitter.split_documents(docs)


def ingest_pdf(file_bytes: bytes, filename: str) -> int:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        docs = _load_pdf(tmp_path)
        today = date.today().isoformat()
        for doc in docs:
            doc.metadata["source"] = filename
            doc.metadata["uploaded_at"] = today
        chunks = _chunk(docs)
        add_documents(chunks)
        return len(chunks)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
