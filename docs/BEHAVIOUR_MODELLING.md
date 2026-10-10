# NextMove — Behaviour Modelling Module

> **Backend Domain Module for Competitor Behaviour Feature Extraction, Sequence Analysis, and Statistical Modelling**

---

## 1. Module Purpose & Architecture

The **Behaviour Modelling** module provides deterministic, statistical, and sequence-based analysis of observed competitor signals. It operates entirely independently of any LLM provider or external AI model checkpoints, ensuring clean separation of concerns.

### Architecture Overview

```
                          ┌───────────────────────────┐
                          │   Historical Evidence     │
                          │   (InMemory / Hindsight)  │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │     BehaviourService      │
                          │ (Statistical & Sequential)│
                          └─────────────┬─────────────┘
                                        │
               ┌────────────────────────┼────────────────────────┐
               ▼                        ▼                        ▼
     ┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐
     │ Action Frequencies│    │ 1st-Order Markov  │    │ Temporal Stats &  │
     │ & Provenance      │    │ Sequence Matrix   │    │ Recurring Patterns│
     └───────────────────┘    └───────────────────┘    └───────────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │CompetitorBehaviourProfile │
                          │     (Pydantic Schema)     │
                          └─────────────┬─────────────┘
                                        │
                         ┌──────────────┴──────────────┐
                         ▼                             ▼
              ┌─────────────────────┐       ┌──────────────────────┐
              │  FastAPI Endpoints  │       │  Future Qwen Prompt  │
              │  (/api/v1/behaviour)│       │  Context Injector    │
              └─────────────────────┘       └──────────────────────┘
```

---

## 2. Mathematical Formulations

1. **1st-Order Markov Transition Probabilities**:
   Given chronological evidence sequence \(E = [e_1, e_2, \dots, e_N]\), where each event \(e_i\) has a strategic cluster \(C(e_i)\):
   \[
   P(C_{t+1} = c_j \mid C_t = c_i) = \frac{\text{Count}(c_i \to c_j)}{\sum_k \text{Count}(c_i \to c_k)}
   \]

2. **Shannon Entropy (Action Predictability)**:
   Measures the randomness vs. consistency of competitor strategic moves:
   \[
   H(X) = -\sum_{i=1}^{K} p_i \log_2(p_i)
   \]
   - \(H(X) = 0.0\): Competitor always performs the exact same strategic action.
   - High \(H(X)\): Competitor moves unpredictably across all 5 strategic clusters.

3. **Wilson Score 95% Confidence Interval for Cluster Proportions**:
   Used to report statistical uncertainty for observed cluster ratios \(\hat{p} = \frac{k}{N}\) with \(z = 1.96\):
   \[
   \text{CI} = \frac{\hat{p} + \frac{z^2}{2N} \pm z \sqrt{\frac{\hat{p}(1-\hat{p})}{N} + \frac{z^2}{4N^2}}}{1 + \frac{z^2}{N}}
   \]

4. **Low Sample Warning**:
   If sample size \(N < 5\), `low_sample_warning` is explicitly set to `True` to alert downstream consumers (e.g. Qwen or analysts) of high statistical uncertainty.

---

## 3. Files Created & Modified

### Created Files
- [`backend/app/schemas/behaviour.py`](file:///c:/Users/bobba/Documents/nextmove/next-move/backend/app/schemas/behaviour.py): Pydantic data schemas.
- [`backend/app/services/behaviour_service.py`](file:///c:/Users/bobba/Documents/nextmove/next-move/backend/app/services/behaviour_service.py): Standalone behaviour modelling domain engine.
- [`backend/app/api/v1/behaviour.py`](file:///c:/Users/bobba/Documents/nextmove/next-move/backend/app/api/v1/behaviour.py): FastAPI API router.
- [`backend/tests/test_behaviour_service.py`](file:///c:/Users/bobba/Documents/nextmove/next-move/backend/tests/test_behaviour_service.py): Unit test suite for behaviour service logic.
- [`backend/tests/test_behaviour_api.py`](file:///c:/Users/bobba/Documents/nextmove/next-move/backend/tests/test_behaviour_api.py): Integration test suite for API endpoints.
- [`docs/BEHAVIOUR_MODELLING.md`](file:///c:/Users/bobba/Documents/nextmove/next-move/docs/BEHAVIOUR_MODELLING.md): Module documentation & Qwen handoff guide.

### Modified Files
- [`backend/app/main.py`](file:///c:/Users/bobba/Documents/nextmove/next-move/backend/app/main.py): Included and mounted `behaviour_router` under `/api/v1/behaviour`.
- [`backend/tests/test_llm_service.py`](file:///c:/Users/bobba/Documents/nextmove/next-move/backend/tests/test_llm_service.py): Fixed test fixture Settings instantiation keyword capitalization.

---

## 4. API Endpoints & Python Signatures

### Python Service Signature
```python
from app.services.behaviour_service import BehaviourService

service = BehaviourService()
profile = service.analyze_evidence(
    competitor_id=competitor_id,
    evidence_list=evidence_list,
    competitor_name="Acme Corp",
    start_date=start_datetime,
    cutoff_date=cutoff_datetime
)
```

### FastAPI Endpoints

#### 1. `POST /api/v1/behaviour/analyze`
Analyze competitor behaviour for a given competitor ID.

- **Request Body**:
```json
{
  "competitor_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "start_date": "2025-01-01T00:00:00Z",
  "cutoff_date": "2025-12-31T23:59:59Z"
}
```

#### 2. `GET /api/v1/behaviour/competitor/{competitor_id}`
Fetch computed behaviour profile for a stored competitor.

- **Sample Response Payload (`200 OK`)**:
```json
{
  "profile": {
    "competitor_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "competitor_name": "Acme Corp",
    "sample_size": 6,
    "provenance_breakdown": {
      "verified": 4,
      "unverified": 1,
      "synthetic": 1
    },
    "cluster_frequencies": [
      {
        "cluster": "Pricing, Promotions & Retail Media",
        "count": 3,
        "percentage": 50.0
      },
      {
        "cluster": "Logistics, Fulfillment & Expansion",
        "count": 3,
        "percentage": 50.0
      }
    ],
    "transition_matrix": [
      {
        "from_cluster": "Pricing, Promotions & Retail Media",
        "to_cluster": "Logistics, Fulfillment & Expansion",
        "count": 3,
        "probability": 1.0
      }
    ],
    "temporal_stats": {
      "total_observations": 6,
      "first_observed": "2025-01-01T12:00:00Z",
      "last_observed": "2025-01-16T12:00:00Z",
      "time_span_days": 15.0,
      "avg_days_between_events": 3.0,
      "event_velocity_per_day": 0.4
    },
    "recurring_patterns": [
      {
        "pattern_id": "PAT_001_PRICING_PROMOTIONS_TO_LOGISTICS_FULFILLMENT",
        "sequence": [
          "Pricing, Promotions & Retail Media",
          "Logistics, Fulfillment & Expansion"
        ],
        "occurrences": 3,
        "avg_interval_days": 6.0,
        "evidence_ids": [
          "e1111111-1111-1111-1111-111111111111",
          "e2222222-2222-2222-2222-222222222222"
        ]
      }
    ],
    "entropy_score": 1.0,
    "confidence_intervals": [
      {
        "cluster": "Pricing, Promotions & Retail Media",
        "proportion": 0.5,
        "ci_lower": 0.1876,
        "ci_upper": 0.8124
      }
    ],
    "low_sample_warning": false,
    "backing_evidence_ids": [
      "e1111111-1111-1111-1111-111111111111",
      "e2222222-2222-2222-2222-222222222222"
    ],
    "analyzed_at": "2026-10-10T14:50:00Z"
  },
  "request_id": "a9b8c7d6-e5f4-4321-8765-123456789abc"
}
```

---

## 5. Qwen LLM Integration Guide

When your teammate integrates the fine-tuned Qwen model (trained on 115,000 samples), they can consume the output of this module as a structured prompt context.

### Example Integration Helper (Python)

```python
def build_qwen_prompt(profile: CompetitorBehaviourProfile) -> str:
    """Format behaviour profile into a structured prompt for Qwen."""
    freq_summary = ", ".join([f"{f.cluster.value}: {f.percentage}% ({f.count} events)" for f in profile.cluster_frequencies])
    trans_summary = ", ".join([f"{t.from_cluster.value} -> {t.to_cluster.value} (P={t.probability})" for t in profile.transition_matrix])
    
    prompt = f"""
    [COMPETITOR BEHAVIOURAL PROFILE]
    Competitor: {profile.competitor_name or profile.competitor_id}
    Sample Size: {profile.sample_size} observations
    Data Quality: {profile.provenance_breakdown.verified} verified, {profile.provenance_breakdown.synthetic} synthetic
    Statistical Predictability (Entropy): {profile.entropy_score} bits
    Low Sample Warning: {profile.low_sample_warning}
    
    Action Frequencies: {freq_summary}
    Transition Probabilities: {trans_summary}
    Temporal Span: {profile.temporal_stats.time_span_days} days (Avg gap: {profile.temporal_stats.avg_days_between_events} days)
    
    Recurring Patterns: {len(profile.recurring_patterns)} detected
    
    Based on the empirical behavioural profile above, analyze the likely strategic objective and next moves for this competitor.
    """
    return prompt.strip()
```

---

## 6. Execution & Test Verification Results

### Running Unit & API Tests

```powershell
# Run behaviour tests only
python -m pytest tests/test_behaviour_service.py tests/test_behaviour_api.py -v

# Run full backend test suite
python -m pytest tests/ -v
```

### Actual Test Verification Output

```
collected 80 items

tests/test_api_v1.py::test_register_competitor PASSED                    [  1%]
tests/test_api_v1.py::test_get_competitor PASSED                         [  2%]
tests/test_api_v1.py::test_get_unknown_competitor PASSED                 [  3%]
tests/test_api_v1.py::test_duplicate_competitor PASSED                   [  5%]
tests/test_api_v1.py::test_request_prediction PASSED                     [  6%]
tests/test_api_v1.py::test_get_prediction PASSED                         [  7%]
tests/test_api_v1.py::test_get_unknown_prediction PASSED                 [  8%]
tests/test_api_v1.py::test_register_evidence PASSED                      [ 10%]
tests/test_behaviour_api.py::test_get_competitor_behaviour_not_found PASSED [ 11%]
tests/test_behaviour_api.py::test_post_analyze_behaviour_not_found PASSED [ 12%]
tests/test_behaviour_api.py::test_get_competitor_behaviour_success PASSED [ 13%]
tests/test_behaviour_api.py::test_post_analyze_behaviour_success PASSED  [ 15%]
tests/test_behaviour_service.py::test_empty_evidence PASSED              [ 16%]
tests/test_behaviour_service.py::test_single_evidence PASSED             [ 17%]
tests/test_behaviour_service.py::test_multiple_evidence_and_transitions PASSED [ 18%]
tests/test_behaviour_service.py::test_recurring_patterns PASSED          [ 20%]
tests/test_behaviour_service.py::test_date_filtering PASSED              [ 21%]
tests/test_behaviour_service.py::test_entropy PASSED                     [ 22%]
...
======================= 79 passed, 1 skipped in 43.24s ========================
```
