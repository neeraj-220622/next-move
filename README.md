# NextMove

> **AI-Powered Competitive Intelligence Platform**

NextMove analyses competitor behaviour, reconstructs historical market signals, predicts potential competitor actions, and learns from previous prediction outcomes.

---

## Architecture Phase Progress

| Phase | Description | Status |
|---|---|---|
| **Phase 1** | Repository foundation and application startup | ✅ Complete |
| **Phase 2** | Basic UI and FastAPI connection | ✅ Complete |
| **Phase 3** | Shared schemas and API contracts | ✅ Complete |
| **Phase 4** | Agent / orchestration layer | ✅ Complete |
| **Phase 5A** | Hindsight memory integration | ✅ Complete |
| **Phase 5B** | Groq LLM integration (openai-compatible) | ✅ Complete |
| **Phase 5C** | Forecasting pipeline (sklearn LogisticRegression) | ✅ Complete |
| **Phase 6** | Configuration, error handling, logging, and resilience | ✅ Complete |
| **Phase 7/8** | Integration verification, RETAIN reliability, hardeneing | ✅ Complete |
| **Phase 9** | Demo Rehearsal and Final Submission Readiness | ✅ Complete |

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

## Next Task — Phase 7

**Goal:** Integration verification and handoff — end-to-end smoke tests, performance validation, and production readiness checklist.

---

## Phase 6 — Completion Report

### What was built

- **Config validation** — `Settings` now validates `LLM_PROVIDER`, `FORECASTING_MODEL`, and timeouts with clear error messages.
- **Secret redaction** — `Settings.safe_summary()` masks `LLM_API_KEY`; never logged or exposed to clients.
- **`DEGRADED` status** — Added to `ServiceStatus` enum; used when sklearn is installed but model artifacts are missing.
- **Request middleware** — Every request logged with method, path, status, duration, and a `X-Request-ID` correlation header.
- **Safe exception handler** — Returns generic `internal_server_error` to clients; full details server-side only.
- **LLM error categorisation** — `generate_explanation` distinguishes `authentication_error` (401), `rate_limit` (429), `timeout`, and `http_error` with safe client messages.
- **Structured logging** — Groq inference latency, forecasting inference latency, model load status, and Hindsight outcomes are logged at appropriate levels.
- **Forecasting metadata** — `check_availability` now reports actual loaded model version and AUC metric.
- **Explicit fallback labelling** — Baseline predictions are always `model_version="baseline"`; sklearn returns `unavailable` when artifacts are missing rather than silently falling back.
- **`evaluate_prediction` documented** — Stub documents why it cannot be implemented (missing `observed_outcome` in schema).
- **70 tests passing** — Includes Phase 6 tests for config validation, secret redaction, LLM error categories, forecasting resilience, status degradation, and Hindsight unavailability.

### Verification

```
Backend tests: 70 passed, 0 failed
/health: HTTP 200
/api/v1/status: HTTP 200, status=ok (all deps up)
Groq smoke test: PASSED (live inference verified)
```

### Configuration reference

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `disabled` | `local`, `openai-compatible`, or `disabled` |
| `LLM_BASE_URL` | `https://api.groq.com/openai/v1` | Base URL of the OpenAI-compatible API |
| `LLM_MODEL` | _(empty)_ | Model name (e.g. `openai/gpt-oss-120b`) |
| `LLM_API_KEY` | _(empty)_ | API key — never logged or echoed |
| `LLM_TIMEOUT` | `30` | Request timeout in seconds |
| `FORECASTING_MODEL` | `baseline` | `baseline`, `sklearn`, or `xgboost` |
| `HINDSIGHT_BASE_URL` | `http://127.0.0.1:8888` | Hindsight memory server URL |
| `HINDSIGHT_TIMEOUT` | `10` | Hindsight timeout in seconds |

### Remaining limitations

- `evaluate_prediction()` requires an `observed_outcome` field not yet in `PredictionResponse`.
- The sklearn model is trained on synthetic data; real-world calibration is unknown.
- The `xgboost` backend has no trained artifacts; it will report `DEGRADED`.

---

## Phase 9 — Completion & Demo Readiness

### 1. Startup Instructions

For a full live demo, three services need to run concurrently:

```powershell
# 1. Start Hindsight (Memory Server)
C:\hs\venv\Scripts\hindsight-api.exe --host 127.0.0.1 --port 8888

# 2. Start Backend
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 3. Start Frontend
cd frontend
npm run dev
```
Navigate to http://localhost:5173 to view the application.

### 2. Demo Scenario & Sample Inputs

1. **Register a Competitor**: Navigate to Competitors and create "Demo Corp".
2. **Submit Evidence**: Enter sample evidence describing recent pricing strategies.
3. **Request Prediction**: Use the "Pricing, Promotions & Retail Media" cluster with a 30-day horizon.
4. **View Results**: The UI will display a probability prediction from the active `sklearn` model (version 1.0.0), a contextual explanation generated by Groq, and request correlation IDs (`X-Request-ID`).

### 3. Forecasting Model Details and Synthetic-Data Limitations

- The backend now actively runs the Phase 5C `sklearn` (Logistic Regression) model.
- Setting `FORECASTING_MODEL=sklearn` enables inference via the `.pkl` artifact.
- **Limitation**: The model is trained purely on synthetic, simulated categorical features. Probabilities returned during the demo do *not* represent real-world predictive accuracy.

### 4. Known Hindsight RETAIN Limitation

- When `RETAIN` attempts to store outcomes into the Hindsight server, Hindsight uses an internal LLM call (via LiteLLM) configured for Groq with `service_tier: auto`.
- The free-tier Groq API key used restricts `service_tier` usage, causing Hindsight's chunk extraction to return a `400 BadRequestError`.
- **Mitigation**: The NextMove coordinator handles this failure gracefully. The primary prediction, explanation, and `RECALL` features still function flawlessly without crashing the request, though memory isn't persistently updated until a local LLM or paid Groq account is configured on the Hindsight server.

### 5. Test Results and Troubleshooting

```
Backend Tests: 70 passed, 0 failed, 0 skipped
```

**Troubleshooting**:
- If predictions fail, ensure `LLM_API_KEY` is present in `backend/.env`.
- If predictions fall back to baseline, ensure `FORECASTING_MODEL=sklearn` is set and artifacts exist in `backend/models/`.
- `X-Request-ID` is safely logged in backend console logs for tracking requests. No secrets are exposed.
