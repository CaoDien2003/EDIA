from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

from app.config import settings

_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)


def require_admin(key: str = Security(_key_header)) -> None:
    if key != settings.admin_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")
