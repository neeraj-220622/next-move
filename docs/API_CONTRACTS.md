# NextMove — API Contracts

## Phase 1: Implemented Endpoints

All endpoints return JSON. Error responses follow the `ErrorDetail` schema.

---

### `GET /health`

**Purpose:** Lightweight liveness probe. Returns 200 if the server process is running.
Does **not** check external dependencies.

**Response `200 OK`:**
```json
{
  "status": "ok",
  "app_name": "NextMove",
  "timestamp": "2026-01-01T00:00:00Z"
}
```

**Schema:** `HealthResponse`
| Field | Type | Notes |
|---|---|---|
| `status` | `string` | Always `"ok"` if the server is up |
| `app_name` | `string` | From `APP_NAME` env var |
| `timestamp` | `datetime` | UTC ISO-8601 |

---

### `GET /api/v1/status`

**Purpose:** Full application and dependency status. Probes Hindsight, LLM, and forecasting subsystems.

**Response `200 OK`:**
```json
{
  "status": "degraded",
  "app_name": "NextMove",
  "app_env": "development",
  "version": "0.1.0",
  "timestamp": "2026-01-01T00:00:00Z",
  "dependencies": [
    {
      "name": "hindsight",
      "status": "unavailable",
      "message": "Connection refused — is Hindsight running at http://localhost:8888?",
      "latency_ms": null
    },
    {
      "name": "llm",
      "status": "unavailable",
      "message": "Connection refused — is the local LLM server running at http://localhost:11434/v1?",
      "latency_ms": null
    },
    {
      "name": "forecasting",
      "status": "ok",
      "message": "Baseline (heuristic) forecasting — no ML dependencies required.",
      "latency_ms": null
    }
  ]
}
```

**Overall `status` values:**
| Value | Meaning |
|---|---|
| `"ok"` | All dependencies healthy |
| `"degraded"` | One or more optional deps unavailable/disabled |
| `"error"` | One or more deps in unknown/error state |

**`ServiceStatus` values for individual dependencies:**
| Value | Meaning |
|---|---|
| `"ok"` | Dependency is reachable and responding |
| `"unavailable"` | Connection refused or timed out |
| `"unknown"` | Unexpected error during probe |
| `"disabled"` | Explicitly disabled in configuration |

---

### `GET /docs`

FastAPI Swagger UI — auto-generated from OpenAPI schema.

### `GET /redoc`

ReDoc documentation UI.

### `GET /openapi.json`

Raw OpenAPI 3.x schema.

---

## Error Response Schema

All endpoints use this schema for errors (HTTP 4xx/5xx):

```json
{
  "error": "internal_server_error",
  "detail": "...",
  "timestamp": "2026-01-01T00:00:00Z"
}
```

| Field | Type | Notes |
|---|---|---|
| `error` | `string` | Machine-readable error code |
| `detail` | `any` | Human-readable detail or validation errors |
| `timestamp` | `datetime` | UTC ISO-8601 |

---

## Phase 2–7: Planned Endpoints (Not Yet Implemented)

These are interface proposals only. Schemas and behaviour will be finalised during implementation.

### `POST /api/v1/competitors` *(Phase 2)*
Register a competitor profile.

### `POST /api/v1/signals` *(Phase 3)*
Submit a competitor signal for analysis.

### `GET /api/v1/analysis/{competitor_id}` *(Phase 3)*
Retrieve behavioural DNA analysis for a competitor.

### `POST /api/v1/predict` *(Phase 4)*
Trigger a prediction run (RECALL → ANALYZE → PREDICT/EXPLAIN → RETAIN).

### `GET /api/v1/predictions` *(Phase 4)*
List past predictions and their current status.

### `GET /api/v1/autopsy/{prediction_id}` *(Phase 5)*
Retrieve a Prediction Autopsy report comparing prediction vs. outcome.

### `GET /api/v1/time-machine` *(Phase 3)*
Query historical signal windows for Strategic Time Machine analysis.

> **Note:** These endpoints are listed for planning purposes only. Do not build against them until they are marked **Implemented** in this document.
