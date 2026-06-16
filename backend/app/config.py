from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(BASE_DIR / ".env"), ".env"),  # project root first, then local
        extra="ignore",
    )

    # ── Database ────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/docai"

    # ── Vector store ────────────────────────────────────────────
    chroma_dir: str = str(BASE_DIR / "data/chroma")

    # ── AI Models ───────────────────────────────────────────────
    embed_model: str = "BAAI/bge-m3"
    llm_backend: str = "local"          # local | groq
    llm_model: str = "Qwen/Qwen3-8B"   # used when llm_backend=local
    groq_api_key: str = ""
    groq_model: str = "llama3-8b-8192"

    # ── RAG ─────────────────────────────────────────────────────
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_new_tokens: int = 512
    top_k: int = 3
    memory_window: int = 5              # last N user+assistant pairs to include

    # ── Auth ────────────────────────────────────────────────────
    admin_key: str = "admin-secret"

    # ── Webhooks ────────────────────────────────────────────────
    webhook_timeout: float = 5.0


settings = Settings()
