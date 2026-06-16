from app.core.llm import get_llm
from app.core.vectorstore import similarity_search
from app.models.conversation import Message

_SYSTEM = (
    "You are a document Q&A assistant. "
    "Answer ONLY based on the provided document context. "
    "Do NOT roleplay as, impersonate, or speak on behalf of any person or company mentioned in the documents. "
    "If the answer is not found in the context, reply: \"I don't have that information in the uploaded documents.\" "
    "Be concise and cite the source document when relevant."
)


def _build_messages(question: str, context: str, history: list[Message]) -> list[dict]:
    messages = [{"role": "system", "content": _SYSTEM}]

    for m in history:
        messages.append({"role": m.role, "content": m.content})

    messages.append({
        "role": "user",
        "content": f"Document context:\n{context}\n\nQuestion: {question}",
    })
    return messages


def answer(question: str, history: list[Message]) -> tuple[str, list[dict]]:
    docs = similarity_search(question)
    if not docs:
        return "I don't have that information in the uploaded documents.", []

    context = "\n\n".join(d.page_content for d in docs)
    messages = _build_messages(question, context, history)
    answer_text = get_llm().generate(messages)

    sources = [
        {"file": d.metadata.get("source", "unknown"), "page": int(d.metadata.get("page", 0))}
        for d in docs
    ]
    return answer_text, sources
