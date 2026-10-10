from fastapi import APIRouter, HTTPException, status
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import List

from app.schemas.competitor import CompetitorCreate, CompetitorResponse
from app.db.repository import competitor_repo

router = APIRouter()

@router.post("/", response_model=CompetitorResponse, status_code=status.HTTP_201_CREATED)
def register_competitor(competitor: CompetitorCreate):
    new_id = uuid4()
    now = datetime.now(timezone.utc)
    
    # Check for duplicate names (simple simulation)
    existing = [c for c in competitor_repo.list_all() if c.name.lower() == competitor.name.lower()]
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Competitor with this name already exists")

    response = CompetitorResponse(
        competitor_id=new_id,
        created_at=now,
        updated_at=now,
        **competitor.model_dump()
    )
    competitor_repo.add(new_id, response)
    return response

@router.get("/", response_model=List[CompetitorResponse])
def list_competitors():
    return competitor_repo.list_all()

@router.get("/{competitor_id}", response_model=CompetitorResponse)
def get_competitor(competitor_id: UUID):
    comp = competitor_repo.get(competitor_id)
    if not comp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")
    return comp
