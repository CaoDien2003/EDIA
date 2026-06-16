from fastapi import APIRouter
from app.api.v1 import analytics, chat, documents, webhooks

router = APIRouter(prefix="/api/v1")
router.include_router(chat.router)
router.include_router(documents.router)
router.include_router(webhooks.router)
router.include_router(analytics.router)
