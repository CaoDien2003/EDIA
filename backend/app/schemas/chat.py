from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    session_id: UUID | None = None


class Source(BaseModel):
    file: str
    page: int


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    session_id: UUID


class MessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    sources: list[Source] | None
    created_at: datetime

    model_config = {"from_attributes": True}
