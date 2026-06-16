import asyncio
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook import Webhook
from app.config import settings


async def fire_event(db: AsyncSession, event_type: str, payload: dict) -> None:
    result = await db.execute(
        select(Webhook).where(Webhook.active.is_(True))
    )
    # Filter by event type in Python — SQLAlchemy base ARRAY.contains() is not implemented
    webhooks = [wh for wh in result.scalars().all() if event_type in (wh.events or [])]
    if not webhooks:
        return

    body = {"event": event_type, "data": payload}

    async def _post(url: str) -> None:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(url, json=body, timeout=settings.webhook_timeout)
        except Exception:
            pass  # fire-and-forget

    await asyncio.gather(*[_post(wh.url) for wh in webhooks])
