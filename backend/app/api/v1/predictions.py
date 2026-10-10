from fastapi import APIRouter, HTTPException, status
from uuid import UUID, uuid4
from typing import List

from app.schemas.prediction import PredictionRequest, PredictionResponse, PredictionStatus
from app.db.repository import prediction_repo, competitor_repo
from app.agents.coordinator import WorkflowCoordinator
from app.agents.adapters import HindsightMemoryAdapter, ForecastingAdapter, LLMAdapter
from app.services.hindsight_service import HindsightService
from app.services.forecasting_service import ForecastingService
from app.services.llm_service import LLMService

router = APIRouter()

@router.post("/", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
async def request_prediction(request: PredictionRequest):
    comp = competitor_repo.get(request.competitor_id)
    if not comp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")

    coordinator = WorkflowCoordinator(
        memory_store=HindsightMemoryAdapter(HindsightService()),
        forecasting_engine=ForecastingAdapter(ForecastingService()),
        explanation_engine=LLMAdapter(LLMService())
    )
    
    response, ctx = await coordinator.execute_prediction(request)
    prediction_repo.add(response.prediction_id, response)
    
    return response

@router.get("/{prediction_id}", response_model=PredictionResponse)
def get_prediction(prediction_id: UUID):
    pred = prediction_repo.get(prediction_id)
    if not pred:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    return pred
