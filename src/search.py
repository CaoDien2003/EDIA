import sys

from src.config import TOP_K
from src.embeddings.embedder import get_embedder
from src.vectorstores.chroma_store import ChromaStore


def search(query: str, k: int = TOP_K) -> None:
    store = ChromaStore(get_embedder())
    results = store.similarity_search(query, k=k)
    for doc in results:
        print("=" * 50)
        print(doc.page_content[:500])


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "What are the models for beam?"
    search(query)
