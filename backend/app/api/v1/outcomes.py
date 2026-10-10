from fastapi import APIRouter, HTTPException, status
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import List

from app.schemas.outcome import (
    PredictionOutcomeCreate,
    PredictionOutcomeResponse,
    EvaluationStatus,
)
from app.db.repository import outcome_repo, prediction_repo

router = APIRouter()


@router.post("/", response_model=PredictionOutcomeResponse, status_code=status.HTTP_201_CREATED)
def register_outcome(outcome: PredictionOutcomeCreate):
    """
    Register an observed outcome for a prediction.
    """
    new_id = uuid4()
    now = datetime.now(timezone.utc)

    response = PredictionOutcomeResponse(
        outcome_id=new_id,
        status=EvaluationStatus.EVALUATED,
        evaluation_time=now,
        **outcome.model_dump(),
    )
    outcome_repo.add(new_id, response)
    return response


@router.get("/prediction/{prediction_id}", response_model=PredictionOutcomeResponse)
def get_outcome_for_prediction(prediction_id: UUID):
    """
    Retrieve recorded outcome for a given prediction ID.
    """
    outcomes = [o for o in outcome_repo.list_all() if o.prediction_id == prediction_id]
    if not outcomes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No outcome recorded for prediction ID {prediction_id}",
        )
    return outcomes[0]
