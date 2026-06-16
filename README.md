# Enterprise Document Intelligence Assistant

A RAG chatbot with conversation memory, structured extraction, webhook integration, and n8n automation. Runs fully local on GPU — no external API required.

## Stack

| Layer | Technology |
|---|---|
| LLM | Qwen3-8B (local, HuggingFace Transformers) — switchable to Groq |
| Embeddings | BGE-M3 (local, sentence-transformers) |
| Vector store | ChromaDB |
| Database | PostgreSQL (conversations, analytics, webhooks) |
| Backend | FastAPI — versioned API (`/api/v1/`) |
| Automation | n8n (self-hosted) |
| Frontend | React + Vite |
| Deployment | Docker Compose |

> Requires a GPU with at least 16 GB VRAM for Qwen3-8B in bfloat16. Tested on A100 80 GB.

---

## Architecture

```
PDF Upload
  → PyMuPDF + chunk splitting
  → BGE-M3 embeddings → ChromaDB
  → PostgreSQL (document metadata)
  → Webhook → n8n (Slack / email)

User Question
  → Load session history (PostgreSQL)
  → ChromaDB similarity search
  → Qwen3-8B with context + memory
  → Save turn to PostgreSQL + analytics event
  → Response with source citations
```

---

## Quick Start

### Local (no Docker)

**1. Backend**

```bash
cd backend
pip install -r requirements.txt
cp ../.env.example ../.env   # set ADMIN_KEY at minimum
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**2. Frontend**

```bash
cd ui
npm install
npm run dev
```

| Service | URL |
|---|---|
| Chat UI | http://localhost:3000 |
| Admin UI | http://localhost:3000/admin |
| API docs | http://localhost:8000/docs |
| n8n | http://localhost:5678 |

---

### Docker Compose (full stack)

```bash
cp .env.example .env    # set ADMIN_KEY and N8N_PASSWORD
docker compose up --build
```

Starts: **PostgreSQL** + **Backend** + **UI** + **n8n**

```bash
docker compose down      # stop, keep data
docker compose down -v   # stop + wipe all volumes
```

---

## API

All endpoints under `/api/v1/`. Admin endpoints require header `X-Admin-Key: <your-key>`.

### Chat

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/chat` | — | Ask a question (optional `session_id`) |
| `GET` | `/api/v1/chat/sessions/{id}/messages` | — | Conversation history |
| `DELETE` | `/api/v1/chat/sessions/{id}` | — | Clear a session |

### Documents

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/documents` | Admin | List all documents |
| `POST` | `/api/v1/documents/upload` | Admin | Upload + index a PDF |
| `DELETE` | `/api/v1/documents/{id}` | Admin | Delete document and its chunks |
| `POST` | `/api/v1/documents/{id}/extract` | Admin | Structured JSON extraction |

### Webhooks

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/webhooks` | Admin | List active webhooks |
| `POST` | `/api/v1/webhooks` | Admin | Register a webhook |
| `DELETE` | `/api/v1/webhooks/{id}` | Admin | Remove a webhook |
| `POST` | `/api/v1/webhooks/test/{id}` | Admin | Send test ping |

### Analytics

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/analytics/summary` | — | 7-day metrics |
| `GET` | `/api/v1/analytics/events` | — | Recent event log |

### Health

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |

---

## Features

### Chat with memory

Each conversation tracks a `session_id`. The last N message pairs are injected into the LLM prompt automatically.

```bash
# New session
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the contract value?"}'

# Continue session
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the penalties?", "session_id": "<uuid>"}'
```

### Structured extraction

```bash
curl -X POST http://localhost:8000/api/v1/documents/<id>/extract \
  -H "X-Admin-Key: your-key"
```

Returns:
```json
{
  "document_id": "...",
  "fields": {
    "parties": ["Company A", "Company B"],
    "effective_date": "2025-01-01",
    "value": 50000,
    "currency": "USD",
    "penalty_clauses": ["Late delivery: 5% per day"],
    "risk_level": "high",
    "risks": ["No limitation of liability clause"]
  }
}
```

If `risk_level` is `"high"`, a `document.high_risk` webhook fires automatically.

### Webhooks

Register any URL to receive push events:

```bash
curl -X POST http://localhost:8000/api/v1/webhooks \
  -H "X-Admin-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "http://localhost:5678/webhook/doc-uploaded", "events": ["document.uploaded"]}'
```

Available events: `document.uploaded`, `document.high_risk`, `chat.completed`

### n8n Automation

Three workflow templates in `n8n/workflows/`:

| File | Trigger | Action |
|---|---|---|
| `document_uploaded_notify.json` | `document.uploaded` | Slack notification |
| `daily_analytics_report.json` | Mon–Fri 8AM | Analytics email report |
| `high_risk_document_alert.json` | `document.high_risk` | Slack alert + escalation |

Import: n8n UI → Workflows → Import from file

---

## Admin Panel

Navigate directly to `http://localhost:3000/admin`. The link is intentionally not exposed in the chat UI.

Authenticate with `ADMIN_KEY`. Features:
- Upload and index PDF documents
- Delete documents
- Run structured extraction
- View analytics

---

## Configuration

`.env` (copy from `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection |
| `LLM_BACKEND` | `local` | `local` (Qwen3 on GPU) or `groq` |
| `LLM_MODEL` | `Qwen/Qwen3-8B` | HuggingFace model ID |
| `GROQ_API_KEY` | — | Required only when `LLM_BACKEND=groq` |
| `GROQ_MODEL` | `llama3-8b-8192` | Groq model name |
| `EMBED_MODEL` | `BAAI/bge-m3` | Embedding model |
| `MAX_NEW_TOKENS` | `512` | Max tokens per LLM response |
| `CHUNK_SIZE` | `1000` | PDF chunk size in characters |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `TOP_K` | `3` | Retrieved chunks per query |
| `MEMORY_WINDOW` | `5` | Conversation pairs in prompt |
| `ADMIN_KEY` | `admin-secret` | Header `X-Admin-Key` for admin routes |
| `N8N_PASSWORD` | `n8n-secret` | n8n basic auth password |
| `WEBHOOK_TIMEOUT` | `5.0` | Outbound webhook timeout (seconds) |

---

## Project Structure

```
pdf-ai-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app + lifespan (table creation, model warmup)
│   │   ├── config.py          # pydantic-settings — all env vars
│   │   ├── database.py        # async SQLAlchemy engine + session factory
│   │   ├── models/            # ORM: document, conversation, analytics, webhook
│   │   ├── schemas/           # Pydantic: chat, document, webhook
│   │   ├── api/
│   │   │   ├── deps.py        # Admin key auth dependency
│   │   │   └── v1/            # Versioned routes
│   │   ├── services/
│   │   │   ├── rag.py         # Retrieval + prompt building
│   │   │   ├── ingest.py      # PDF → chunks → ChromaDB
│   │   │   ├── memory.py      # Session + conversation history
│   │   │   ├── extraction.py  # Structured JSON extraction
│   │   │   └── webhook.py     # Outbound fire-and-forget webhooks
│   │   └── core/
│   │       ├── llm.py         # Qwen3 / Groq abstraction
│   │       ├── embeddings.py  # BGE-M3
│   │       └── vectorstore.py # ChromaDB wrapper
│   ├── Dockerfile
│   └── requirements.txt
├── n8n/
│   ├── workflows/             # Ready-to-import n8n workflow JSONs
│   └── setup_workflows.py     # Script to create workflows via n8n REST API
├── ui/
│   └── src/pages/
│       ├── Chat.jsx           # Chat interface (session-aware)
│       └── Admin.jsx          # Admin panel (upload, extract, analytics)
├── data/
│   └── chroma/                # ChromaDB vector store (persisted)
├── docker-compose.yml
├── Dockerfile.ui              # React build → nginx
└── .env.example
```

---

## Database Schema

```
documents   — indexed PDF files (name, chunk_count, status)
sessions    — chat sessions
messages    — conversation turns (role, content, sources JSONB)
events      — analytics log (event_type, duration_ms, metadata JSONB)
webhooks    — registered outbound URLs + subscribed events
```

Tables are created automatically on first startup — no migration needed in development.

## 🤝 Connect With Me

- Email: [nguyencaodien2003@gmail.com](mailto:nguyencaodien2003@gmail.com)
- Phone: +84 396 404 443

[![GitHub](https://img.shields.io/badge/GitHub-CaoDien2003-black?logo=github)](https://github.com/CaoDien2003)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Nguyen%20Cao%20Dien-blue?logo=linkedin)](https://linkedin.com/in/nguyencaodien)
