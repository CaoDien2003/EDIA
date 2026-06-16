import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

PDF_DIR = BASE_DIR / "data/raw_pdf"
CHROMA_DIR = BASE_DIR / "data/chroma"

EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-m3")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen3-8B")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "512"))
TOP_K = int(os.getenv("TOP_K", "3"))

API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = int(os.getenv("API_PORT", "8000"))

ADMIN_KEY = os.getenv("ADMIN_KEY", "admin-secret")
