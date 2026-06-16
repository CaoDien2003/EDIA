import time
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.analytics import Event
from app.models.conversation import Message, Session
from app.schemas.chat import ChatRequest, ChatResponse, MessageOut, Source
from app.services import memory, rag, webhook

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)) -> ChatResponse:
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    session = await memory.get_or_create_session(db, req.session_id)
    history = await memory.load_history(db, session.id)

    t0 = time.monotonic()
    answer_text, sources = rag.answer(req.question, history)
    duration_ms = int((time.monotonic() - t0) * 1000)

    await memory.save_turn(db, session.id, req.question, answer_text, sources)
    db.add(Event(
        event_type="chat.completed",
        session_id=session.id,
        duration_ms=duration_ms,
        metadata_={"question_len": len(req.question), "sources": len(sources)},
    ))
    await db.commit()

    await webhook.fire_event(db, "chat.completed", {
        "session_id": str(session.id),
        "question": req.question,
        "duration_ms": duration_ms,
    })

    return ChatResponse(
        answer=answer_text,
        sources=[Source(**s) for s in sources],
        session_id=session.id,
    )


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def get_messages(session_id: UUID, db: AsyncSession = Depends(get_db)):
    return await memory.load_history(db, session_id)


@router.delete("/sessions/{session_id}")
async def clear_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Message).where(Message.session_id == session_id))
    await db.execute(delete(Session).where(Session.id == session_id))
    await db.commit()
    return {"message": f"Session {session_id} cleared"}
