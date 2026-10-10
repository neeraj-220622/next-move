from fastapi import APIRouter, HTTPException, status
from uuid import UUID, uuid4
from typing import List

from app.schemas.evidence import EvidenceCreate, EvidenceResponse, ValidationStatus
from app.db.repository import evidence_repo, competitor_repo

router = APIRouter()

@router.post("/", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
def register_evidence(evidence: EvidenceCreate):
    comp = competitor_repo.get(evidence.competitor_id)
    if not comp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")

    new_id = uuid4()
    response = EvidenceResponse(
        evidence_id=new_id,
        validation_status=ValidationStatus.PENDING,
        **evidence.model_dump()
    )
    evidence_repo.add(new_id, response)
    return response

@router.get("/", response_model=List[EvidenceResponse])
def list_evidence():
    return evidence_repo.list_all()
