# AuraChat: Production-Grade Multi-Turn AI Chatbot

A production-ready, state-of-the-art conversational AI system with **LangGraph orchestration**, **$N$-turn sliding context retention & rolling summarization**, a **hybrid document reading engine**, **async SQLAlchemy 2.0 persistence** (SQLite / PostgreSQL swappable), and a **sleek glassmorphic React/Vite UI**.

---

## 🌟 Key Features

1. **Universal Model Abstraction (LangChain `ChatOpenAI`)**:
   - Seamlessly consumes **Google Gemini** (via OpenAI-compatible endpoint), **NVIDIA NIM**, **OpenAI**, or local **Ollama/vLLM**.
   - Switch models and providers on-the-fly from the live Settings modal.

2. **$N$-Turn Context Retention & Rolling Summarization**:
   - Preserves the most recent $N$ conversational turns ($2N$ messages) in raw fidelity.
   - Older conversational turns are automatically condensed by an LLM node into a running, structured rolling summary, ensuring the context window never bloats or exceeds token limits.

3. **Hybrid Document Ingestion System**:
   - Supports `.pdf`, `.docx`, `.txt`, `.csv`, `.tsv`, `.xlsx`, `.md`, `.json`, `.py`, `.js`, and code files.
   - **Small files** ($\le 2,500$ estimated tokens): Injected directly into the prompt context for zero-latency retrieval.
   - **Large files** ($> 2,500$ estimated tokens): Indexed in a session-scoped BM25 hybrid store and queried on-demand by the model using agentic tools (`search_document`, `read_document_page`, `inspect_document_outline`).

4. **Real-Time Streaming**:
   - Fast Server-Sent Events (SSE) streaming tokens directly to the UI.
   - Full WebSocket channel (`/ws/chat`) featuring `on_resume` conversation reconnection and replay.

5. **Persistence with SQLAlchemy 2.0 (Async)**:
   - Configured via `DATABASE_URL` (SQLite `sqlite+aiosqlite:///./data/app.db` by default, easily swapped to PostgreSQL `postgresql+asyncpg://...`).
   - Automatically initializes tables and indices on startup via FastAPI lifespan hook.

6. **Environment-Configured Authentication**:
   - Configurable users via `APP_USERS="admin:admin123,kvothe:password123"`.
   - Issues signed JWT tokens to isolate conversation threads and documents per user.

---

## 🚀 Quick Start

### 1. Configure Environment Variables
Copy `.env.example` to `.env` or edit `.env`:
```bash
GEMINI_API_KEY="your-gemini-key"
NVIDIA_NIM_KEY="your-nvidia-nim-key"
APP_USERS="admin:admin123,kvothe:password123"
DATABASE_URL="sqlite+aiosqlite:///./data/app.db"
```

### 2. Run Locally

#### Option A: Using the Convenience Runner
```bash
# Start FastAPI backend (port 8000)
./run.sh backend

# In a separate terminal, start React frontend (port 5173)
./run.sh frontend
```

#### Option B: Manual Commands
```bash
# Backend
source .venv/bin/activate
export PYTHONPATH=backend:$PYTHONPATH
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend
npm run dev
```

Visit **http://localhost:5173** to sign in (default credentials: `kvothe` / `password123` or `admin` / `admin123`).

---

## 🧪 Running Automated Tests

Run the complete backend test suite:
```bash
source .venv/bin/activate
PYTHONPATH=backend pytest backend/tests/ -v
```

All 9 test suites cover:
- Authentication & JWT issuance/validation
- Document parsers across `.txt`, `.csv`, `.pdf`, `.docx`
- Hybrid routing heuristic
- $N$-turn summarizer threshold math
- REST API health, auth, and model endpoints

---

## 🐳 Docker Deployment

Run the complete multi-container stack with Docker Compose:
```bash
docker compose up --build
```
- Frontend: **http://localhost:3000**
- Backend: **http://localhost:8000**