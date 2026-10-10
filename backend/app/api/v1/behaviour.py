from fastapi import APIRouter, HTTPException, status, Query
from uuid import UUID, uuid4
from datetime import datetime
from typing import List, Optional

from app.schemas.behaviour import (
    BehaviourAnalysisRequest,
    BehaviourAnalysisResponse,
    CompetitorBehaviourProfile,
)
from app.schemas.evidence import EvidenceResponse
from app.db.repository import competitor_repo, evidence_repo
from app.services.behaviour_service import BehaviourService

router = APIRouter()
behaviour_service = BehaviourService()


@router.post("/analyze", response_model=BehaviourAnalysisResponse)
def analyze_behaviour(request: BehaviourAnalysisRequest):
    """
    Analyze competitor behaviour patterns and feature statistics.

    Retrieves historical evidence for the specified competitor ID and returns
    action frequencies, 1st-order Markov transition probabilities, temporal metrics,
    and recurring pattern signatures.
    """
    comp = competitor_repo.get(request.competitor_id)
    comp_name = comp.name if comp else None

    # Retrieve evidence from repository for this competitor
    all_evidence = [e for e in evidence_repo.list_all() if e.competitor_id == request.competitor_id]

    if not comp and not all_evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor with ID {request.competitor_id} not found and has no recorded evidence.",
        )

    profile = behaviour_service.analyze_evidence(
        competitor_id=request.competitor_id,
        evidence_list=all_evidence,
        competitor_name=comp_name,
        start_date=request.start_date,
        cutoff_date=request.cutoff_date,
    )

    return BehaviourAnalysisResponse(
        profile=profile,
        request_id=str(uuid4()),
    )


@router.get("/competitor/{competitor_id}", response_model=BehaviourAnalysisResponse)
def get_competitor_behaviour(
    competitor_id: UUID,
    start_date: Optional[datetime] = Query(None, description="Filter lower bound observation timestamp"),
    cutoff_date: Optional[datetime] = Query(None, description="Filter upper bound observation timestamp"),
):
    """
    Fetch calculated Behaviour Profile for a stored competitor.
    """
    comp = competitor_repo.get(competitor_id)
    comp_name = comp.name if comp else None

    all_evidence = [e for e in evidence_repo.list_all() if e.competitor_id == competitor_id]

    if not comp and not all_evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor with ID {competitor_id} not found.",
        )

    profile = behaviour_service.analyze_evidence(
        competitor_id=competitor_id,
        evidence_list=all_evidence,
        competitor_name=comp_name,
        start_date=start_date,
        cutoff_date=cutoff_date,
    )

    return BehaviourAnalysisResponse(
        profile=profile,
        request_id=str(uuid4()),
    )
