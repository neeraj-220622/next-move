# NextMove — Strategic Time Machine Module

> **Backend Domain Module for Historical Timeline Replay, Step-by-Step Simulation, and Leakage-Free Backtesting**

---

## 1. Module Purpose & Architecture

The **Strategic Time Machine** module allows analysts and automated evaluation pipelines to perform leak-safe timeline replays across historical time windows. It simulates what the system would have known, predicted, and recommended at any discrete point in history without lookahead bias.

### Architecture Overview

```
                               ┌───────────────────────────┐
                               │   Historical Evidence &   │
                               │   Prediction Outcomes     │
                               └─────────────┬─────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │   TimeMachineService      │
                               │  (Timeline Simulation)    │
                               └─────────────┬─────────────┘
                                             │
               ┌─────────────────────────────┼─────────────────────────────┐
               ▼                             ▼                             ▼
    ┌────────────────────┐        ┌────────────────────┐        ┌────────────────────┐
    │ Filter Evidence    │        │ Compute Historical │        │ Run Leak-Safe      │
    │ (observation_time  │        │ Behaviour Profile  │        │ Forecast Inference │
    │   <= cutoff_date)  │        │ (at cutoff_date)   │        │ (at cutoff_date)   │
    └────────────────────┘        └────────────────────┘        └────────────────────┘
               │                             │                             │
               └─────────────────────────────┼─────────────────────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │   TimeMachineSnapshot     │
                               │ (Behavior + Forecast +    │
                               │   Evaluated Outcome)      │
                               └─────────────┬─────────────┘
                                             │
                              ┌──────────────┴──────────────┐
                              ▼                             ▼
                   ┌─────────────────────┐       ┌──────────────────────┐
                   │  FastAPI Endpoints  │       │  Future Qwen Prompt  │
                   │ (/timemachine &     │       │  Context Injector    │
                   │  /outcomes)         │       │  (Timeline Replay)   │
                   └─────────────────────┘       └──────────────────────┘
```

---

## 2. Key Concepts & Leakage-Prevention Principles

1. **Event Time vs. Information Availability Time**:
   - `observation_time`: Timestamp when the event actually occurred or was published in the real world.
   - `ingestion_time`: Timestamp when the record entered the database.
   - *Rule*: Timeline snapshots use `observation_time <= cutoff_date` as the strict cutoff boundary. Evidence published after `cutoff_date` is strictly excluded from that snapshot.

2. **Counterfactual Outcome Matching**:
   - Actual outcomes (`PredictionOutcomeResponse`) recorded during `[cutoff_date, cutoff_date + horizon_days]` are matched *after* prediction inference to evaluate accuracy and compute Brier score:
     \[
     \text{Brier Score} = (p - y)^2
     \]
     where \(p \in [0, 1]\) is the forecast probability and \(y \in \{0.0, 1.0\}\) is the observed binary outcome.

3. **Step-by-Step Replay Progression**:
   - Replays progress chronologically from `start_cutoff` to `end_cutoff` in increments of `step_days` (e.g. every 15 or 30 days).

---

## 3. Files Created & Modified

### Created Files
- [`backend/app/schemas/timemachine.py`](file:///c:/Users/bobba/Documents/nextmove/next-move/backend/app/schemas/timemachine.py): Pydantic data schemas (`TimeMachineReplayRequest`, `TimeMachineSnapshot`, `TimeMachineReplayResponse`).
- [`backend/app/services/timemachine_service.py`](file:///c:/Users/bobba/Documents/nextmove/next-move/backend/app/services/timemachine_service.py): Core TimeMachineService simulation engine.
- [`backend/app/api/v1/outcomes.py`](file:///c:/Users/bobba/Documents/nextmove/next-move/backend/app/api/v1/outcomes.py): API router for registering and retrieving prediction outcomes.
- [`backend/app/api/v1/timemachine.py`](file:///c:/Users/bobba/Documents/nextmove/next-move/backend/app/api/v1/timemachine.py): API router for executing and querying timeline replays.
- [`backend/tests/test_timemachine_service.py`](file:///c:/Users/bobba/Documents/nextmove/next-move/backend/tests/test_timemachine_service.py): Unit test suite for time machine service logic.
- [`backend/tests/test_timemachine_api.py`](file:///c:/Users/bobba/Documents/nextmove/next-move/backend/tests/test_timemachine_api.py): Integration test suite for outcomes & timemachine API endpoints.
- [`docs/STRATEGIC_TIME_MACHINE.md`](file:///c:/Users/bobba/Documents/nextmove/next-move/docs/STRATEGIC_TIME_MACHINE.md): Technical architecture documentation & Qwen integration guide.

### Modified Files
- [`backend/app/db/repository.py`](file:///c:/Users/bobba/Documents/nextmove/next-move/backend/app/db/repository.py): Added `outcome_repo` and `timemachine_repo` global in-memory stores.
- [`backend/app/main.py`](file:///c:/Users/bobba/Documents/nextmove/next-move/backend/app/main.py): Included and mounted `outcomes_router` (`/api/v1/outcomes`) and `timemachine_router` (`/api/v1/timemachine`).

---

## 4. API Endpoints & Python Signatures

### Python Service Signature
```python
from app.services.timemachine_service import TimeMachineService
from app.schemas.timemachine import TimeMachineReplayRequest

tm_service = TimeMachineService()
req = TimeMachineReplayRequest(
    competitor_id=competitor_id,
    start_cutoff=datetime(2025, 1, 1, tzinfo=timezone.utc),
    end_cutoff=datetime(2025, 6, 1, tzinfo=timezone.utc),
    step_days=30,
    horizon_days=30
)

replay_res = tm_service.run_replay(
    request=req,
    evidence_list=evidence_list,
    outcomes_list=outcomes_list,
    competitor_name="Acme Corp"
)
```

### FastAPI Endpoints

#### 1. `POST /api/v1/outcomes/`
Register an observed event outcome for a prediction.

- **Request Body**:
```json
{
  "prediction_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "occurrence": "occurred",
  "window_start": "2025-01-01T00:00:00Z",
  "window_end": "2025-02-01T00:00:00Z"
}
```

#### 2. `POST /api/v1/timemachine/replay`
Execute a timeline replay simulation over a historical time window.

- **Request Body**:
```json
{
  "competitor_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "start_cutoff": "2025-01-01T00:00:00Z",
  "end_cutoff": "2025-03-01T00:00:00Z",
  "step_days": 30,
  "horizon_days": 30
}
```

- **Sample Response Payload (`201 Created`)**:
```json
{
  "replay_id": "b1111111-2222-3333-4444-555555555555",
  "competitor_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "start_cutoff": "2025-01-01T00:00:00Z",
  "end_cutoff": "2025-03-01T00:00:00Z",
  "step_days": 30,
  "horizon_days": 30,
  "snapshots": [
    {
      "snapshot_id": "s1111111-1111-1111-1111-111111111111",
      "cutoff_date": "2025-01-01T00:00:00Z",
      "available_evidence_count": 2,
      "behaviour_profile": { ... },
      "prediction": {
        "prediction_id": "p1111111-1111-1111-1111-111111111111",
        "competitor_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "cluster": "Pricing, Promotions & Retail Media",
        "cutoff_date": "2025-01-01T00:00:00Z",
        "horizon_days": 30,
        "probability": 0.6,
        "model_version": "baseline",
        "status": "completed"
      },
      "outcome": {
        "prediction_id": "p1111111-1111-1111-1111-111111111111",
        "occurrence": "occurred",
        "window_start": "2025-01-01T00:00:00Z",
        "window_end": "2025-02-01T00:00:00Z"
      },
      "brier_score": 0.16,
      "accuracy": 1.0
    }
  ],
  "mean_brier_score": 0.16,
  "mean_accuracy": 1.0,
  "total_snapshots": 3,
  "created_at": "2026-10-10T15:25:00Z"
}
```

---

## 5. Qwen LLM Integration Guide

When your teammate connects Qwen to the Strategic Time Machine output, Qwen can generate historical backtest narratives or analyze strategy evolution over time using the snapshot sequence:

```python
def build_qwen_timemachine_prompt(replay: TimeMachineReplayResponse) -> str:
    """Format Time Machine timeline replay into a prompt context for Qwen."""
    lines = [
        f"[STRATEGIC TIME MACHINE REPLAY]",
        f"Competitor ID: {replay.competitor_id}",
        f"Simulation Range: {replay.start_cutoff.date()} to {replay.end_cutoff.date()} (Step: {replay.step_days} days)",
        f"Total Snapshots: {replay.total_snapshots}",
        f"Overall Backtest Accuracy: {replay.mean_accuracy if replay.mean_accuracy is not None else 'N/A'}",
        f"Overall Brier Error Score: {replay.mean_brier_score if replay.mean_brier_score is not None else 'N/A'}",
        "",
        "CHRONOLOGICAL SNAPSHOT TRAJECTORY:"
    ]
    
    for i, snap in enumerate(replay.snapshots, 1):
        lines.append(
            f"Snapshot {i} ({snap.cutoff_date.date()}): "
            f"Evidence Count={snap.available_evidence_count} | "
            f"Top Cluster={snap.behaviour_profile.cluster_frequencies[0].cluster.value if snap.behaviour_profile.cluster_frequencies else 'None'} | "
            f"Forecast Prob={snap.prediction.probability} | "
            f"Outcome={snap.outcome.occurrence.value if snap.outcome else 'Unobserved'}"
        )
    
    lines.append("\nAnalyze how the competitor's strategic focus evolved across these historical snapshots.")
    return "\n".join(lines)
```

---

## 6. Execution & Test Verification Results

### Running Unit & API Tests

```powershell
# Run timemachine tests only
python -m pytest tests/test_timemachine_service.py tests/test_timemachine_api.py -v

# Run full backend test suite
python -m pytest tests/ -v
```

### Actual Test Verification Output

```
collected 88 items

tests/test_api_v1.py::test_register_competitor PASSED                    [  1%]
...
tests/test_behaviour_api.py::test_post_analyze_behaviour_success PASSED  [ 13%]
tests/test_behaviour_service.py::test_empty_evidence PASSED              [ 14%]
...
tests/test_timemachine_api.py::test_outcome_registration_and_retrieval PASSED [ 92%]
tests/test_timemachine_api.py::test_outcome_not_found PASSED             [ 93%]
tests/test_timemachine_api.py::test_timemachine_replay_not_found PASSED  [ 94%]
tests/test_timemachine_api.py::test_timemachine_replay_invalid_cutoff PASSED [ 95%]
tests/test_timemachine_api.py::test_timemachine_replay_success PASSED    [ 96%]
tests/test_timemachine_service.py::test_invalid_cutoff_range PASSED      [ 97%]
tests/test_timemachine_service.py::test_timeline_evidence_growth_and_snapshots PASSED [ 98%]
tests/test_timemachine_service.py::test_outcome_matching_and_evaluation PASSED [100%]

======================= 87 passed, 1 skipped in 58.86s ========================
```
