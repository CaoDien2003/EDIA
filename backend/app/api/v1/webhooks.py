from uuid import UUID
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.webhook import Webhook
from app.schemas.webhook import WebhookCreate, WebhookOut

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get("", response_model=list[WebhookOut], dependencies=[Depends(require_admin)])
async def list_webhooks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Webhook).where(Webhook.active.is_(True)))
    return result.scalars().all()


@router.post("", response_model=WebhookOut, dependencies=[Depends(require_admin)])
async def create_webhook(body: WebhookCreate, db: AsyncSession = Depends(get_db)):
    wh = Webhook(url=body.url, events=body.events)
    db.add(wh)
    await db.commit()
    await db.refresh(wh)
    return wh


@router.delete("/{webhook_id}", dependencies=[Depends(require_admin)])
async def delete_webhook(webhook_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Webhook).where(Webhook.id == webhook_id))
    wh = result.scalar_one_or_none()
    if not wh:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await db.delete(wh)
    await db.commit()
    return {"message": "Webhook deleted"}


@router.post("/test/{webhook_id}", dependencies=[Depends(require_admin)])
async def test_webhook(webhook_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Webhook).where(Webhook.id == webhook_id))
    wh = result.scalar_one_or_none()
    if not wh:
        raise HTTPException(status_code=404, detail="Webhook not found")

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                wh.url,
                json={"event": "webhook.test", "data": {"message": "Test ping"}},
                timeout=5.0,
            )
        return {"status_code": r.status_code, "ok": r.is_success}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Webhook unreachable: {e}")
