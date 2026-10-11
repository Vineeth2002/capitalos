from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.claim import Claim
from app.schemas.claim_evidence import ClaimEvidenceCreate, ClaimEvidenceResponse
from app.services import claim_evidence_service
from app.services.claim_evidence_service import ClaimEvidenceError

router = APIRouter(tags=["claim-evidence"])


@router.post(
    "/claims/{claim_id}/evidence", response_model=ClaimEvidenceResponse, status_code=201
)
def attach_claim_evidence(
    claim_id: int, evidence_in: ClaimEvidenceCreate, db: Session = Depends(get_db)
):
    try:
        return claim_evidence_service.attach_evidence(db, claim_id, evidence_in)
    except ClaimEvidenceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/claims/{claim_id}/evidence", response_model=list[ClaimEvidenceResponse])
def list_claim_evidence(claim_id: int, db: Session = Depends(get_db)):
    claim = db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim_evidence_service.list_evidence_for_claim(db, claim_id)


@router.delete("/claims/{claim_id}/evidence/{evidence_id}", status_code=204)
def detach_claim_evidence(claim_id: int, evidence_id: int, db: Session = Depends(get_db)):
    evidence = claim_evidence_service.get_claim_evidence(db, claim_id, evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found for this claim")
    claim_evidence_service.detach_evidence(db, evidence)
    return None