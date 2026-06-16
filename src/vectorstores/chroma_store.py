from langchain_community.vectorstores import Chroma

from src.config import CHROMA_DIR


class ChromaStore:

    def __init__(self, embedding):
        self._db = Chroma(
            persist_directory=str(CHROMA_DIR),
            embedding_function=embedding,
        )

    def add_documents(self, docs: list) -> None:
        self._db.add_documents(docs)

    def similarity_search(self, query: str, k: int) -> list:
        return self._db.similarity_search(query, k=k)

    def list_sources(self) -> list[dict]:
        result = self._db.get(include=["metadatas"])
        seen: dict = {}
        for meta in result.get("metadatas") or []:
            if meta and "source" in meta:
                src = meta["source"]
                if src not in seen:
                    seen[src] = meta.get("uploaded_at", "unknown")
        return [{"name": k, "uploaded_at": v} for k, v in seen.items()]

    def delete_by_source(self, source_name: str) -> int:
        result = self._db.get(where={"source": source_name})
        ids = result.get("ids") or []
        if ids:
            self._db.delete(ids=ids)
        return len(ids)
