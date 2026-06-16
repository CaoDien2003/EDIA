from functools import lru_cache
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from app.config import settings
from app.core.embeddings import get_embedder


@lru_cache(maxsize=1)
def _store() -> Chroma:
    return Chroma(
        persist_directory=settings.chroma_dir,
        embedding_function=get_embedder(),
    )


def add_documents(docs: list[Document]) -> None:
    _store().add_documents(docs)


def similarity_search(query: str, k: int | None = None) -> list[Document]:
    return _store().similarity_search(query, k=k or settings.top_k)


def delete_by_source(source_name: str) -> int:
    store = _store()
    result = store.get(where={"source": source_name})
    ids = result.get("ids") or []
    if ids:
        store.delete(ids=ids)
    return len(ids)
