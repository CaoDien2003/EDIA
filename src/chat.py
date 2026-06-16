from src.config import TOP_K
from src.embeddings.embedder import get_embedder
from src.llm.qwen import QwenLLM
from src.vectorstores.chroma_store import ChromaStore

PROMPT_TEMPLATE = """Answer based only on the context below. If the answer is not in the context, say you don't know.

Context:
{context}

Question:
{question}"""


def answer(question: str) -> str:
    store = ChromaStore(get_embedder())
    docs = store.similarity_search(question, k=TOP_K)
    context = "\n\n".join(d.page_content for d in docs)
    prompt = PROMPT_TEMPLATE.format(context=context, question=question)
    return QwenLLM().generate(prompt)


if __name__ == "__main__":
    question = input("Question: ")
    print("\nAnswer:\n")
    print(answer(question))
