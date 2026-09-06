from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entity import Entity
from app.models.research_case import ResearchCase
from app.models.claim import Claim
from app.schemas.claim import ClaimCreate, ClaimUpdate, ClaimResponse
from app.services import claim_service

router = APIRouter(tags=["claims"])


@router.post("/research-cases/{case_id}/claims", response_model=ClaimResponse)
def create_claim(case_id: int, claim_in: ClaimCreate, db: Session = Depends(get_db)):
    case = db.get(ResearchCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Research case not found")
    if claim_in.entity_id is not None:
        entity = db.get(Entity, claim_in.entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
    return claim_service.create_claim(db, case_id, claim_in)


@router.get("/research-cases/{case_id}/claims", response_model=list[ClaimResponse])
def list_case_claims(case_id: int, db: Session = Depends(get_db)):
    case = db.get(ResearchCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Research case not found")
    return claim_service.list_case_claims(db, case_id)


@router.get("/claims/{claim_id}", response_model=ClaimResponse)
def get_claim(claim_id: int, db: Session = Depends(get_db)):
    claim = claim_service.get_claim(db, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@router.patch("/claims/{claim_id}", response_model=ClaimResponse)
def update_claim(claim_id: int, claim_in: ClaimUpdate, db: Session = Depends(get_db)):
    claim = claim_service.get_claim(db, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim_in.entity_id is not None:
        entity = db.get(Entity, claim_in.entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
    return claim_service.update_claim(db, claim, claim_in)