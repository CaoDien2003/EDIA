from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: UUID
    name: str
    size_bytes: int | None
    chunk_count: int
    status: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class ExtractionResult(BaseModel):
    document_id: UUID
    fields: dict
