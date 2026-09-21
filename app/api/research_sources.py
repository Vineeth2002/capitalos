from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.claim import Claim
from app.schemas.research_source import ResearchSourceCreate, ResearchSourceResponse
from app.schemas.claim_source import ClaimSourceCreate, ClaimSourceResponse
from app.services import research_source_service

router = APIRouter(tags=["research-sources"])


@router.post(
    "/research-sources", response_model=ResearchSourceResponse, status_code=201
)
def create_research_source(
    source_in: ResearchSourceCreate, db: Session = Depends(get_db)
):
    return research_source_service.create_source(db, source_in)


@router.get("/research-sources", response_model=list[ResearchSourceResponse])
def list_research_sources(db: Session = Depends(get_db)):
    return research_source_service.list_sources(db)


@router.get("/research-sources/{source_id}", response_model=ResearchSourceResponse)
def get_research_source(source_id: int, db: Session = Depends(get_db)):
    source = research_source_service.get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.get(
    "/research-sources/{source_id}/claims", response_model=list[ClaimSourceResponse]
)
def list_claims_for_source(source_id: int, db: Session = Depends(get_db)):
    source = research_source_service.get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return research_source_service.list_claims_for_source(db, source_id)


@router.post(
    "/claims/{claim_id}/sources", response_model=ClaimSourceResponse, status_code=201
)
def attach_source_to_claim(
    claim_id: int, attach_in: ClaimSourceCreate, db: Session = Depends(get_db)
):
    claim = db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    source = research_source_service.get_source(db, attach_in.source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    if research_source_service.claim_source_exists(db, claim_id, attach_in.source_id):
        raise HTTPException(
            status_code=409, detail="This source is already attached to this claim"
        )

    return research_source_service.attach_source_to_claim(db, claim_id, attach_in)


@router.get("/claims/{claim_id}/sources", response_model=list[ClaimSourceResponse])
def list_sources_for_claim(claim_id: int, db: Session = Depends(get_db)):
    claim = db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return research_source_service.list_sources_for_claim(db, claim_id)


@router.delete("/claims/{claim_id}/sources/{source_id}", status_code=204)
def detach_source_from_claim(
    claim_id: int, source_id: int, db: Session = Depends(get_db)
):
    claim_source = research_source_service.get_claim_source(db, claim_id, source_id)
    if not claim_source:
        raise HTTPException(
            status_code=404, detail="This source is not attached to this claim"
        )
    research_source_service.detach_source_from_claim(db, claim_source)
    return None