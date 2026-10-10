from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from typing import List, Optional

from app.schemas.timemachine import (
    TimeMachineReplayRequest,
    TimeMachineReplayResponse,
)
from app.db.repository import (
    competitor_repo,
    evidence_repo,
    outcome_repo,
    timemachine_repo,
)
from app.services.timemachine_service import TimeMachineService

router = APIRouter()
timemachine_service = TimeMachineService()


@router.post("/replay", response_model=TimeMachineReplayResponse, status_code=status.HTTP_201_CREATED)
def execute_replay(request: TimeMachineReplayRequest):
    """
    Execute a Strategic Time Machine timeline replay simulation over a historical time window.
    """
    comp = competitor_repo.get(request.competitor_id)
    comp_name = comp.name if comp else None

    all_evidence = [e for e in evidence_repo.list_all() if e.competitor_id == request.competitor_id]

    if not comp and not all_evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor with ID {request.competitor_id} not found and has no recorded evidence.",
        )

    all_outcomes = outcome_repo.list_all()

    try:
        replay_res = timemachine_service.run_replay(
            request=request,
            evidence_list=all_evidence,
            outcomes_list=all_outcomes,
            competitor_name=comp_name,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    timemachine_repo.add(replay_res.replay_id, replay_res)
    return replay_res


@router.get("/replay/{replay_id}", response_model=TimeMachineReplayResponse)
def get_replay_result(replay_id: UUID):
    """
    Retrieve stored Time Machine replay simulation results by ID.
    """
    replay = timemachine_repo.get(replay_id)
    if not replay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Replay simulation with ID {replay_id} not found.",
        )
    return replay
