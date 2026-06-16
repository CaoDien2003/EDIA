from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class WebhookCreate(BaseModel):
    url: str
    events: list[str]


class WebhookOut(BaseModel):
    id: UUID
    url: str
    events: list[str]
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
