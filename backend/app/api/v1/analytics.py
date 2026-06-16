from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.analytics import Event
from app.models.document import Document

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def summary(db: AsyncSession = Depends(get_db)):
    since = datetime.now(timezone.utc) - timedelta(days=7)

    total_queries = await db.scalar(
        select(func.count()).where(
            Event.event_type == "chat.completed",
            Event.created_at >= since,
        )
    ) or 0

    avg_duration = await db.scalar(
        select(func.avg(Event.duration_ms)).where(
            Event.event_type == "chat.completed",
            Event.created_at >= since,
        )
    )

    total_uploads = await db.scalar(
        select(func.count()).where(
            Event.event_type == "document.uploaded",
            Event.created_at >= since,
        )
    ) or 0

    total_documents = await db.scalar(select(func.count()).select_from(Document)) or 0

    return {
        "period": "last_7_days",
        "total_queries": total_queries,
        "avg_response_ms": round(avg_duration or 0),
        "total_uploads": total_uploads,
        "total_documents": total_documents,
    }


@router.get("/events")
async def list_events(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Event).order_by(Event.created_at.desc()).limit(limit)
    )
    return [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "duration_ms": e.duration_ms,
            "metadata": e.metadata_,
            "created_at": e.created_at.isoformat(),
        }
        for e in result.scalars().all()
    ]
