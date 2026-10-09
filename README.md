# NextMove

> **AI-Powered Competitive Intelligence Platform**

NextMove analyses competitor behaviour, reconstructs historical market signals, predicts potential competitor actions, and learns from previous prediction outcomes.

---

## Architecture Phase Progress

| Phase | Description | Status |
|---|---|---|
| **Phase 1** | Repository foundation and application startup | ✅ Complete |
| **Phase 2** | Basic UI and FastAPI connection | 🔲 Pending |
| **Phase 3** | Shared schemas and API contracts | 🔲 Pending |
| **Phase 4** | Agent / orchestration layer | 🔲 Pending |
| **Phase 5** | Hindsight and local Qwen integration | 🔲 Pending |
| **Phase 6** | Configuration, errors, logging, and resilience | 🔲 Pending |
| **Phase 7** | Integration verification and handoff | 🔲 Pending |

---

## Phase 1 — Completion Report

### What was built

- Git repository initialised.
- FastAPI backend with `/health`, `/api/v1/status`, `/docs`, CORS, logging.
- Pydantic-settings centralised configuration reading from `.env`.
- `HindsightService` — connectivity probe + Phase 5 interface stubs.
- `LLMService` — provider-agnostic connectivity probe + Phase 5 stubs.
- `ForecastingService` — backend availability check + Phase 4/5 stubs.
- React + Vite + TypeScript + Tailwind CSS frontend.
- Real backend connection polling with three states: connecting / connected / error.
- Backend test suite (pytest) — 11 tests, all passing.
- Frontend Vite build — passes.
- `docs/ARCHITECTURE.md` and `docs/API_CONTRACTS.md`.
- PowerShell helper scripts in `scripts/`.

### Verification

```
Backend tests: 11 passed
Frontend build: passed (vite build)
Backend startup: confirmed
```

### Known issues / prerequisites

- **Hindsight server** — not running by default; `/api/v1/status` will report `hindsight: unavailable`. Start separately when ready.
- **Local LLM** — not running by default; `llm: unavailable` is expected. Configure `LLM_BASE_URL` and start Ollama/LM Studio when ready.
- The three feature screens (Behavioral DNA, Time Machine, Autopsy) are placeholder cards. Full UI is planned for Phase 2.

---

## Repository Structure

```
NextMove/
├── README.md
├── .gitignore
├── .env.example
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── api/
│   │   │   └── health.py        # GET /health  GET /api/v1/status
│   │   ├── core/
│   │   │   └── config.py        # Pydantic-settings configuration
│   │   ├── schemas/
│   │   │   └── common.py        # Shared request/response schemas
│   │   └── services/
│   │       ├── hindsight_service.py
│   │       ├── llm_service.py
│   │       └── forecasting_service.py
│   ├── tests/
│   │   └── test_health.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/          # StatusPanel, FeatureCard, Header
│   │   ├── services/api.ts      # All HTTP calls to FastAPI
│   │   ├── types/api.ts         # TypeScript types (mirrors backend schemas)
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
├── docs/
│   ├── ARCHITECTURE.md
│   └── API_CONTRACTS.md
└── scripts/
    ├── start_backend.ps1
    ├── start_frontend.ps1
    └── run_tests.ps1
```

---

## Setup Instructions (Windows PowerShell)

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Git

### 1. Clone and configure environment

```powershell
git clone <repo-url>
cd NextMove

# Backend environment
Copy-Item backend\.env.example backend\.env
# Edit backend\.env if needed

# Frontend environment  
Copy-Item frontend\.env.example frontend\.env.local
# Leave VITE_API_BASE_URL empty to use the Vite proxy (recommended)
```

### 2. Backend — create virtual environment and install dependencies

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
```

### 3. Start FastAPI

```powershell
# From backend/ with venv active:
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Or use the helper script from repo root:
.\scripts\start_backend.ps1
```

Swagger UI: http://localhost:8000/docs

### 4. Frontend — install dependencies

```powershell
cd frontend
npm install
```

### 5. Start Vite dev server

```powershell
# From frontend/:
npm run dev

# Or use the helper script from repo root:
.\scripts\start_frontend.ps1
```

Frontend: http://localhost:5173

### 6. Run backend tests

```powershell
# From backend/ with venv active:
pytest tests/ -v

# Or use the helper script from repo root:
.\scripts\run_tests.ps1
```

> **No live services required.** Tests mock all external calls.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, Uvicorn, Pydantic v2 |
| Frontend | React 18, Vite, TypeScript, Tailwind CSS v4 |
| Memory | Hindsight server (Phase 5) |
| LLM | Qwen via local OpenAI-compatible endpoint (Phase 5) |
| Forecasting | scikit-learn / XGBoost (Phase 4/5) |
| Testing | pytest, pytest-asyncio, httpx |
| Config | pydantic-settings, python-dotenv |

---

## Next Task — Phase 2

**Goal:** Expand the UI with real navigation between the three feature pages and wire up the FastAPI connection indicator more prominently. Add shared TypeScript types matching the API contract schemas.

**Exact next step:**
> Implement the Phase 2 UI: create dedicated React route pages for Behavioral DNA, Strategic Time Machine, and Prediction Autopsy. Each page should display the backend connection status and make a real API call. Add React Router and define the route structure.
