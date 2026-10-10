# NextMove — API Contracts

## Phase 1 & 2: Health & Status

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
      "message": "Connection refused",
      "latency_ms": null
    }
  ]
}
```

---

## Phase 3: Core Business Entities (Development Stubs)

The following endpoints are functional using an **in-memory repository**. Data is wiped on server restart.

### `GET /api/v1/competitors/`
List registered competitors.

**Response `200 OK`:** Array of `CompetitorResponse` objects.

### `POST /api/v1/competitors/`
Register a competitor profile.

**Request Body (`CompetitorCreate`):**
```json
{
  "name": "Amazon",
  "website": "https://amazon.com",
  "description": "Retail giant",
  "tracked_clusters": ["Logistics, Fulfillment & Expansion"]
}
```

**Response `201 Created`:** `CompetitorResponse` object with generated `competitor_id` and timestamps. Returns `409 Conflict` if the name exists.

### `GET /api/v1/competitors/{competitor_id}`
Retrieve a competitor by stable UUID. Returns `404` if not found.

---

### `POST /api/v1/predict/`
Submit a prediction request. Currently returns an explicit **unavailable** state since no forecasting models are integrated yet.

**Request Body (`PredictionRequest`):**
```json
{
  "competitor_id": "uuid",
  "cluster": "Pricing, Promotions & Retail Media",
  "cutoff_date": "2026-01-01T00:00:00Z",
  "horizon_days": 30,
  "evidence_ids": [],
  "metadata": {}
}
```

**Response `201 Created`:**
```json
{
  "prediction_id": "uuid",
  "competitor_id": "uuid",
  "cluster": "Pricing, Promotions & Retail Media",
  "cutoff_date": "2026-01-01T00:00:00Z",
  "horizon_days": 30,
  "probability": null,
  "model_version": null,
  "evidence_ids": [],
  "created_at": "2026-01-01T00:00:00Z",
  "status": "unavailable"
}
```

### `GET /api/v1/predict/{prediction_id}`
Retrieve a saved prediction. Returns `404` if not found.

---

### `POST /api/v1/evidence/`
Register an evidence record with provenance and timestamp validation.

**Request Body (`EvidenceCreate`):**
```json
{
  "competitor_id": "uuid",
  "cluster": "Marketplace & Seller Operations",
  "description": "Seller fee changes announced",
  "source_url": "https://news.example.com/...",
  "observation_time": "2026-01-01T00:00:00Z",
  "provenance": "unverified",
  "confidence": null
}
```

**Response `201 Created`:** `EvidenceResponse` object. Returns `404` if the `competitor_id` is unknown.

### `GET /api/v1/evidence/`
List all registered evidence.

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

## Phase 4–7: Planned Endpoints (Not Yet Implemented)

- **Prediction Analysis Pipeline:** Connecting the `/api/v1/predict/` endpoint to the forecasting service.
- **Hindsight Integration:** Endpoints to store and retrieve memory objects (`MemoryReference`) backed by the Hindsight server.
- **Prediction Autopsy (`GET /api/v1/autopsy/{prediction_id}`):** Retrieve a Prediction Autopsy report comparing prediction vs. outcome.
