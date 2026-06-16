import json
from app.core.llm import get_llm
from app.core.vectorstore import similarity_search

_SYSTEM = "You are a data extraction assistant. Return ONLY valid JSON — no explanation, no markdown fences, no extra text."

_USER_TMPL = """\
Extract the following fields from the document context as JSON.

Fields:
- parties: list of company/person names
- effective_date: ISO date string or null
- value: monetary amount as number or null
- currency: currency code or null
- penalty_clauses: list of penalty descriptions
- risk_level: "low" | "medium" | "high"
- risks: list of identified risk descriptions

Context:
{context}

JSON:"""


def extract_from_document(source_name: str) -> dict:
    docs = similarity_search("contract parties dates value penalties risks", k=10)
    relevant = [d for d in docs if d.metadata.get("source") == source_name] or docs[:5]

    context = "\n\n".join(d.page_content for d in relevant[:5])
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": _USER_TMPL.format(context=context)},
    ]
    raw = get_llm().generate(messages)

    try:
        start, end = raw.find("{"), raw.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(raw[start:end])
    except json.JSONDecodeError:
        pass

    return {"raw_output": raw, "error": "Could not parse structured JSON from LLM output"}
