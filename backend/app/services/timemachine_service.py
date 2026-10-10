from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from app.schemas.evidence import EvidenceResponse
from app.schemas.outcome import PredictionOutcomeResponse, EventOccurrence
from app.schemas.prediction import PredictionResponse, PredictionStatus
from app.schemas.cluster import StrategicCluster
from app.schemas.timemachine import (
    TimeMachineReplayRequest,
    TimeMachineSnapshot,
    TimeMachineReplayResponse,
)
from app.services.behaviour_service import BehaviourService
from app.services.forecasting_service import ForecastingService
from app.db.repository import competitor_repo, evidence_repo, outcome_repo, prediction_repo


class TimeMachineService:
    """
    Core domain service for Strategic Time Machine timeline replays & counterfactual evaluation.
    Executes leak-safe step-by-step historical simulation across discrete cutoff timestamps.
    """

    def __init__(
        self,
        behaviour_service: Optional[BehaviourService] = None,
        forecasting_service: Optional[ForecastingService] = None,
    ):
        self.behaviour_service = behaviour_service or BehaviourService()
        self.forecasting_service = forecasting_service or ForecastingService()

    def run_replay(
        self,
        request: TimeMachineReplayRequest,
        evidence_list: List[EvidenceResponse],
        outcomes_list: Optional[List[PredictionOutcomeResponse]] = None,
        competitor_name: Optional[str] = None,
    ) -> TimeMachineReplayResponse:
        """
        Execute a timeline replay simulation over the specified cutoff window.

        Parameters
        ----------
        request : TimeMachineReplayRequest
            Simulation request parameters (start_cutoff, end_cutoff, step_days, horizon_days).
        evidence_list : List[EvidenceResponse]
            List of evidence observations.
        outcomes_list : Optional[List[PredictionOutcomeResponse]]
            Optional list of recorded prediction outcomes for accuracy evaluation.
        competitor_name : Optional[str]
            Optional competitor display name.
        """
        if request.start_cutoff > request.end_cutoff:
            raise ValueError("start_cutoff cannot be later than end_cutoff")

        # Generate discrete step cutoff timestamps
        cutoff_dates: List[datetime] = []
        curr = request.start_cutoff
        step_delta = timedelta(days=request.step_days)

        while curr <= request.end_cutoff:
            cutoff_dates.append(curr)
            curr += step_delta

        if cutoff_dates and cutoff_dates[-1] < request.end_cutoff:
            cutoff_dates.append(request.end_cutoff)

        snapshots: List[TimeMachineSnapshot] = []
        brier_scores: List[float] = []
        accuracies: List[float] = []

        outcomes_by_pred_id = {o.prediction_id: o for o in (outcomes_list or [])}

        for cutoff in cutoff_dates:
            # 1. Leakage-safe evidence filtering: ONLY evidence observed up to cutoff
            filtered_evidence = [
                e for e in evidence_list
                if e.competitor_id == request.competitor_id and e.observation_time <= cutoff
            ]

            # 2. Historical Behaviour Profile at cutoff
            behaviour_profile = self.behaviour_service.analyze_evidence(
                competitor_id=request.competitor_id,
                evidence_list=filtered_evidence,
                competitor_name=competitor_name,
                cutoff_date=cutoff,
            )

            # Determine dominant cluster for forecast features
            dominant_cluster = (
                behaviour_profile.cluster_frequencies[0].cluster
                if behaviour_profile.cluster_frequencies
                else StrategicCluster.PRICING_PROMOTIONS
            )

            # 3. Forecast inference for this snapshot cutoff
            features = {
                "evidence_count": len(filtered_evidence),
                "horizon_days": request.horizon_days,
                "cluster": dominant_cluster.name.lower(),
            }
            forecast_result = self.forecasting_service.predict_competitor_action(features)

            prob = forecast_result.get("probability") if forecast_result.get("status") == "ok" else None
            model_ver = forecast_result.get("model_version", "baseline")
            pred_status = PredictionStatus.COMPLETED if prob is not None else PredictionStatus.UNAVAILABLE

            pred_id = uuid4()
            prediction = PredictionResponse(
                prediction_id=pred_id,
                competitor_id=request.competitor_id,
                cluster=dominant_cluster,
                cutoff_date=cutoff,
                horizon_days=request.horizon_days,
                probability=prob,
                model_version=model_ver,
                explanation=f"Time Machine simulated prediction at cutoff {cutoff.isoformat()}.",
                evidence_ids=[e.evidence_id for e in filtered_evidence],
                created_at=cutoff,
                status=pred_status,
            )

            # 4. Outcome matching and evaluation (if available)
            matched_outcome: Optional[PredictionOutcomeResponse] = None
            brier_score: Optional[float] = None
            accuracy: Optional[float] = None

            # Check if an outcome matches the simulation window [cutoff, cutoff + horizon]
            horizon_end = cutoff + timedelta(days=request.horizon_days)
            for o in (outcomes_list or []):
                if o.window_start <= cutoff and o.window_end >= horizon_end:
                    matched_outcome = o
                    break

            if matched_outcome and matched_outcome.occurrence != EventOccurrence.UNKNOWN and prob is not None:
                actual_val = 1.0 if matched_outcome.occurrence == EventOccurrence.OCCURRED else 0.0
                brier_score = round((prob - actual_val) ** 2, 4)
                pred_binary = 1.0 if prob >= 0.5 else 0.0
                accuracy = 1.0 if pred_binary == actual_val else 0.0

                brier_scores.append(brier_score)
                accuracies.append(accuracy)

            snapshots.append(
                TimeMachineSnapshot(
                    snapshot_id=uuid4(),
                    cutoff_date=cutoff,
                    available_evidence_count=len(filtered_evidence),
                    behaviour_profile=behaviour_profile,
                    prediction=prediction,
                    outcome=matched_outcome,
                    brier_score=brier_score,
                    accuracy=accuracy,
                )
            )

        mean_brier = round(sum(brier_scores) / len(brier_scores), 4) if brier_scores else None
        mean_acc = round(sum(accuracies) / len(accuracies), 4) if accuracies else None

        return TimeMachineReplayResponse(
            replay_id=uuid4(),
            competitor_id=request.competitor_id,
            start_cutoff=request.start_cutoff,
            end_cutoff=request.end_cutoff,
            step_days=request.step_days,
            horizon_days=request.horizon_days,
            snapshots=snapshots,
            mean_brier_score=mean_brier,
            mean_accuracy=mean_acc,
            total_snapshots=len(snapshots),
        )
