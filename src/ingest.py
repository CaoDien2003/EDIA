import sys
from datetime import date
from pathlib import Path

from src.config import PDF_DIR
from src.embeddings.embedder import get_embedder
from src.loaders.pdf_loader import load_pdf
from src.utils.chunker import Chunker
from src.vectorstores.chroma_store import ChromaStore


def ingest(pdf_path: str, store: ChromaStore, original_name: str | None = None) -> int:
    docs = load_pdf(pdf_path)
    filename = original_name or Path(pdf_path).name
    today = date.today().isoformat()
    for doc in docs:
        doc.metadata["source"] = filename
        doc.metadata["uploaded_at"] = today
    chunks = Chunker().split(docs)
    store.add_documents(chunks)
    return len(chunks)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else str(PDF_DIR / "sample.pdf")
    store = ChromaStore(get_embedder())
    count = ingest(path, store)
    print(f"Indexed {count} chunks from {path}")
