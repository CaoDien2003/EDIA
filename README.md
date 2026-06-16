# PDF AI Assistant

A fully local RAG system with separate Admin and User flows. No external API required — everything runs on your own hardware.

![Architecture](docs/architecture.png)

- **LLM**: Qwen3-8B (local, HuggingFace Transformers)
- **Embeddings**: BGE-M3 (local, sentence-transformers)
- **Vector store**: ChromaDB
- **Backend**: FastAPI
- **Frontend**: React + Vite (served by nginx in Docker)

> Because the LLM runs locally, this project requires a GPU with at least 16 GB VRAM. Cloud platforms like Railway or Render do not provide GPU and cannot run this stack.

---

## Requirements

- Python 3.10+
- Node.js 20+
- GPU with at least 16 GB VRAM (Qwen3-8B in bfloat16)

---

## Run locally (no Docker)

### Backend

```bash
pip install -r requirements.txt
cp .env.example .env        # set ADMIN_KEY
uvicorn api.app:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd ui
cp .env.example .env        # VITE_API_URL=http://localhost:8000
npm install
npm run dev
```

- Chat UI: `http://localhost:3000`
- Admin UI: `http://localhost:3000/admin`
- API docs: `http://localhost:8000/docs`

---

## Run with Docker Compose

```bash
cp .env.example .env        # set ADMIN_KEY
docker compose up --build
```

- Chat UI: `http://localhost:3000`
- Admin UI: `http://localhost:3000/admin`
- API: `http://localhost:8000`

> `VITE_API_URL` in `docker-compose.yml` is baked into the React build at compile time and must be the URL the **browser** can reach. For a VPS, replace `localhost` with your domain or IP.

ChromaDB data persists in a Docker volume (`chroma_data`).

```bash
docker compose down          # stop (keep data)
docker compose down -v       # stop + delete all indexed documents
```

---

## Usage

### User

Open `http://<host>:3000` — type a question, get an answer. Each response includes a **Sources** toggle showing which file and page the answer came from.

### Admin

Navigate to `http://<host>:3000/admin` (not linked from the chat UI). Enter the `ADMIN_KEY` to access:

- **Upload** — select a PDF, click "Upload & Index". Chunking and embedding happen immediately.
- **Documents** — view all indexed files with upload date.
- **Delete** — remove a document and all its chunks from the vector store.

### CLI tools

```bash
# Ingest a PDF directly (no server needed)
python -m src.ingest data/raw_pdf/your_file.pdf

# CLI chat
python -m src.chat

# Debug similarity search
python -m src.search "your query"
```

---

## Configuration

### Backend (`.env`)

| Variable | Default | Description |
|---|---|---|
| `LLM_MODEL` | `Qwen/Qwen3-8B` | HuggingFace causal LLM (~16 GB VRAM) |
| `MAX_NEW_TOKENS` | `512` | Max tokens generated per answer |
| `EMBED_MODEL` | `BAAI/bge-m3` | HuggingFace embedding model (~2 GB RAM) |
| `CHUNK_SIZE` | `1000` | Characters per chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `TOP_K` | `3` | Retrieved chunks per query |
| `ADMIN_KEY` | `admin-secret` | Secret key for `/admin/*` endpoints |

### Frontend (`ui/.env`)

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | Backend URL (must be reachable from the browser) |

---

## Project structure

```
pdf-ai-assistant/
├── api/
│   └── app.py                  # FastAPI (user chat + admin routes)
├── src/
│   ├── config.py
│   ├── ingest.py
│   ├── chat.py
│   ├── search.py
│   ├── embeddings/embedder.py
│   ├── llm/qwen.py
│   ├── loaders/pdf_loader.py
│   ├── utils/chunker.py
│   └── vectorstores/chroma_store.py
├── ui/
│   ├── src/
│   │   ├── App.jsx             # Routes: / and /admin
│   │   ├── main.jsx
│   │   ├── index.css
│   │   └── pages/
│   │       ├── Chat.jsx        # User chat (ChatGPT-style)
│   │       └── Admin.jsx       # Admin panel (login-gated, hidden URL)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── nginx.conf              # Serves React build in Docker
├── docs/
│   └── architecture.png
├── scripts/
│   └── gen_diagram.py
├── data/raw_pdf/
├── Dockerfile                  # API container
├── Dockerfile.ui               # React build → nginx container
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## API reference

### `POST /chat`

```json
{ "question": "What is the return policy?" }
```
```json
{ "answer": "...", "sources": [{ "file": "faq.pdf", "page": 2 }] }
```

### Admin — header `X-Admin-Key: <your-key>`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/admin/documents` | List all indexed documents |
| `POST` | `/admin/upload` | Upload + index a PDF (`multipart/form-data`, field `file`) |
| `DELETE` | `/admin/documents/{name}` | Remove all chunks for a document |
