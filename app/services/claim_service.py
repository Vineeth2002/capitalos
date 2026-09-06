from sqlalchemy.orm import Session

from app.models.claim import Claim
from app.schemas.claim import ClaimCreate, ClaimUpdate


def create_claim(db: Session, case_id: int, claim_in: ClaimCreate) -> Claim:
    claim = Claim(research_case_id=case_id, **claim_in.model_dump())
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim


def get_claim(db: Session, claim_id: int) -> Claim | None:
    return db.get(Claim, claim_id)


def list_case_claims(db: Session, case_id: int) -> list[Claim]:
    return db.query(Claim).filter(Claim.research_case_id == case_id).all()


def update_claim(db: Session, claim: Claim, claim_in: ClaimUpdate) -> Claim:
    update_data = claim_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(claim, field, value)
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim