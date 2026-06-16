from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.vectorstore import delete_by_source
from app.database import get_db
from app.models.analytics import Event
from app.models.document import Document
from app.schemas.document import DocumentOut, ExtractionResult
from app.services import extraction, ingest, webhook

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut], dependencies=[Depends(require_admin)])
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).order_by(Document.uploaded_at.desc()))
    return result.scalars().all()


@router.post("/upload", response_model=DocumentOut, dependencies=[Depends(require_admin)])
async def upload_document(file: UploadFile, db: AsyncSession = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    chunk_count = ingest.ingest_pdf(content, file.filename)

    # Upsert: re-uploading the same filename replaces the old record
    existing = await db.execute(select(Document).where(Document.name == file.filename))
    doc = existing.scalar_one_or_none()
    if doc:
        doc.size_bytes = len(content)
        doc.chunk_count = chunk_count
        doc.status = "indexed"
    else:
        doc = Document(name=file.filename, size_bytes=len(content), chunk_count=chunk_count)
        db.add(doc)
    db.add(Event(
        event_type="document.uploaded",
        metadata_={"filename": file.filename, "chunk_count": chunk_count},
    ))
    await db.commit()
    await db.refresh(doc)

    await webhook.fire_event(db, "document.uploaded", {
        "document_id": str(doc.id),
        "filename": file.filename,
        "chunk_count": chunk_count,
    })
    return doc


@router.delete("/{document_id}", dependencies=[Depends(require_admin)])
async def delete_document(document_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    deleted = delete_by_source(doc.name)
    await db.delete(doc)
    await db.commit()
    return {"message": f"Deleted {deleted} chunks from {doc.name}"}


@router.post("/{document_id}/extract", response_model=ExtractionResult, dependencies=[Depends(require_admin)])
async def extract_document(document_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    fields = extraction.extract_from_document(doc.name)

    risk = fields.get("risk_level", "unknown")
    if risk == "high":
        await webhook.fire_event(db, "document.high_risk", {
            "document_id": str(doc.id),
            "filename": doc.name,
            "risk_level": risk,
            "risks": fields.get("risks", []),
        })

    return ExtractionResult(document_id=document_id, fields=fields)
