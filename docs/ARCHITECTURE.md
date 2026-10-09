# NextMove — Architecture Documentation

## 1. System Overview

NextMove is an AI-powered competitive intelligence platform with three core product features:

| Feature | Purpose |
|---|---|
| **Competitor Behavioral DNA** | Identify and remember recurring competitor behaviours |
| **Strategic Time Machine** | Reconstruct historical signals; evaluate pre-move predictability |
| **Prediction Autopsy** | Compare predictions with outcomes; feed lessons back into forecasting |

---

## 2. Component Responsibilities

```
┌─────────────────────────────────────────────────────┐
│                    React Frontend                    │
│  (Vite + TypeScript + Tailwind CSS)                  │
│  Displays competitor analysis, predictions, history  │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP (JSON)
                       ▼
┌─────────────────────────────────────────────────────┐
│                FastAPI Backend                       │
│  ┌────────────┐  ┌─────────────────────────────┐    │
│  │  API Layer  │  │   Agent/Orchestration Layer  │    │
│  │  (routers) │  │   (Phase 4 — planned)        │    │
│  └──────┬─────┘  └──────────┬──────────────────┘    │
│         │                   │                        │
│  ┌──────▼──────────────────▼──────────────────┐     │
│  │              Service Layer                  │     │
│  │  ┌──────────────┐  ┌────────────────────┐  │     │
│  │  │  Hindsight   │  │    LLM Service     │  │     │
│  │  │  Service     │  │  (Qwen / local)    │  │     │
│  │  └──────────────┘  └────────────────────┘  │     │
│  │  ┌──────────────────────────────────────┐  │     │
│  │  │        Forecasting Service           │  │     │
│  │  │  (baseline → sklearn → xgboost)     │  │     │
│  │  └──────────────────────────────────────┘  │     │
│  └─────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────┘
                       │
          ┌────────────┴─────────────┐
          ▼                          ▼
┌─────────────────┐       ┌──────────────────────┐
│ Hindsight Server│       │  Local LLM Runtime   │
│ (localhost:8888)│       │  (Ollama / LM Studio)│
│ Memory & recall │       │  Qwen model          │
└─────────────────┘       └──────────────────────┘
```

---

## 3. Service Responsibilities (Strict Separation)

### 3.1 Hindsight Service (`hindsight_service.py`)
- **Responsibility:** Persistent memory — store and retrieve competitor signals and prediction outcomes.
- **Not responsible for:** Generating text, producing numerical predictions.
- **Key operations (Phase 5):** `store_evidence`, `recall_relevant`, `retain_outcome`.
- **Isolation:** All SDK/HTTP calls are encapsulated here. No other module constructs Hindsight URLs.

### 3.2 LLM Service (`llm_service.py`)
- **Responsibility:** Natural-language explanation generation.
- **Not responsible for:** Storing memories, computing probabilities.
- **Key operations (Phase 5):** `generate_explanation`, `summarise_evidence`.
- **Provider isolation:** Swapping Qwen ↔ OpenAI-compatible requires only a settings change.

### 3.3 Forecasting Service (`forecasting_service.py`)
- **Responsibility:** Numerical prediction — probability estimates and outcome evaluation.
- **Not responsible for:** Memory retrieval, explanation generation.
- **Key operations (Phase 4/5):** `predict_competitor_action`, `evaluate_prediction`.
- **Backend isolation:** `baseline`, `sklearn`, and `xgboost` backends are interchangeable.

---

## 4. RECALL → ANALYZE → PREDICT/EXPLAIN → RETAIN Workflow

This is the planned intelligence pipeline (Phase 4+). It is **not yet implemented**.

```
Input: competitor signal / analysis request
      │
      ▼
  ┌──────────────────────────────────────┐
  │  RECALL                              │
  │  HindsightService.recall_relevant()  │
  │  Retrieve past similar signals       │
  └──────────────────┬───────────────────┘
                     │
                     ▼
  ┌──────────────────────────────────────┐
  │  ANALYZE                             │
  │  ForecastingService.predict_*()      │
  │  Combine recalled context + features │
  │  to produce probability estimates    │
  └──────────────────┬───────────────────┘
                     │
                     ▼
  ┌──────────────────────────────────────┐
  │  EXPLAIN                             │
  │  LLMService.generate_explanation()   │
  │  Wrap numerical prediction in        │
  │  natural-language rationale          │
  └──────────────────┬───────────────────┘
                     │
                     ▼
  ┌──────────────────────────────────────┐
  │  RETAIN                              │
  │  HindsightService.retain_outcome()   │
  │  Store prediction + outcome for      │
  │  future Prediction Autopsy           │
  └──────────────────────────────────────┘
```

---

## 5. How Product Features Use Shared Services

| Feature | Hindsight | LLM | Forecasting |
|---|---|---|---|
| **Behavioral DNA** | `recall_relevant` (pattern matching) | `summarise_evidence` | `predict_competitor_action` |
| **Strategic Time Machine** | `recall_relevant` (historical window) | `generate_explanation` | `predict_competitor_action` (retrodictive) |
| **Prediction Autopsy** | `retain_outcome`, `recall_relevant` | `generate_explanation` (lesson summary) | `evaluate_prediction` |

---

## 6. Frontend ↔ Backend Communication

- **Protocol:** HTTP/JSON over REST.
- **Base URL:** Configurable via `VITE_API_BASE_URL` (empty = Vite proxy).
- **Auth:** None in Phase 1. Token-based auth is planned for Phase 6.
- **Error handling:** Backend returns structured `ErrorDetail` JSON; frontend shows honest connection states.

---

## 7. Implementation Status

### ✅ Implemented (Phase 1)

| Component | Status |
|---|---|
| Repository structure | ✅ Complete |
| `.env.example` | ✅ Complete |
| FastAPI application | ✅ Running |
| `GET /health` | ✅ Implemented & tested |
| `GET /api/v1/status` | ✅ Implemented & tested |
| CORS configuration | ✅ Complete |
| Centralised settings | ✅ Complete |
| HindsightService (interface + connectivity probe) | ✅ Phase 1 done |
| LLMService (interface + connectivity probe) | ✅ Phase 1 done |
| ForecastingService (interface + availability check) | ✅ Phase 1 done |
| React + Vite + TypeScript + Tailwind frontend | ✅ Running |
| Backend status indicator in UI | ✅ Complete |
| Backend tests | ✅ Passing |
| Architecture documentation | ✅ This file |

### 🔲 Planned (Later Phases)

| Component | Target Phase |
|---|---|
| Agent / orchestration layer | Phase 4 |
| `HindsightService.store_evidence` | Phase 5 |
| `HindsightService.recall_relevant` | Phase 5 |
| `HindsightService.retain_outcome` | Phase 5 |
| `LLMService.generate_explanation` | Phase 5 |
| `ForecastingService.predict_competitor_action` | Phase 4/5 |
| Feature UI screens (DNA, Time Machine, Autopsy) | Phase 2/3 |
| Authentication | Phase 6 |
| Production deployment | Phase 7 |
