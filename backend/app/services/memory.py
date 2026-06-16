from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Session, Message
from app.config import settings


async def get_or_create_session(db: AsyncSession, session_id: UUID | None) -> Session:
    if session_id:
        result = await db.execute(select(Session).where(Session.id == session_id))
        existing = result.scalar_one_or_none()
        if existing:
            return existing
    session = Session()
    db.add(session)
    await db.flush()
    return session


async def load_history(db: AsyncSession, session_id: UUID) -> list[Message]:
    limit = settings.memory_window * 2
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    return list(reversed(result.scalars().all()))


async def save_turn(
    db: AsyncSession,
    session_id: UUID,
    question: str,
    answer: str,
    sources: list[dict],
) -> None:
    db.add(Message(session_id=session_id, role="user", content=question))
    db.add(Message(session_id=session_id, role="assistant", content=answer, sources=sources))
    await db.flush()
