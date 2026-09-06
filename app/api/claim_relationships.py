from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.claim import Claim
from app.schemas.claim_relationship import (
    ClaimRelationshipCreate,
    ClaimRelationshipResponse,
)
from app.services import claim_relationship_service

router = APIRouter(tags=["claim-relationships"])


@router.post(
    "/claims/{claim_id}/relationships", response_model=ClaimRelationshipResponse
)
def create_relationship(
    claim_id: int,
    relationship_in: ClaimRelationshipCreate,
    db: Session = Depends(get_db),
):
    from_claim = db.get(Claim, claim_id)
    if not from_claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    to_claim = db.get(Claim, relationship_in.to_claim_id)
    if not to_claim:
        raise HTTPException(status_code=404, detail="Target claim not found")

    if claim_id == relationship_in.to_claim_id:
        raise HTTPException(
            status_code=422, detail="A claim cannot have a relationship to itself"
        )

    return claim_relationship_service.create_relationship(
        db, claim_id, relationship_in
    )


@router.get(
    "/claims/{claim_id}/relationships", response_model=list[ClaimRelationshipResponse]
)
def list_relationships(claim_id: int, db: Session = Depends(get_db)):
    claim = db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    return claim_relationship_service.list_claim_relationships(db, claim_id)