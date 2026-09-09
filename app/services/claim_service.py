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

from app.models.claim_relationship import ClaimRelationship
from app.models.challenge_output import ChallengeOutputClaim


def claim_has_dependencies(db: Session, claim_id: int) -> bool:
    relationship_exists = (
        db.query(ClaimRelationship)
        .filter(
            (ClaimRelationship.from_claim_id == claim_id)
            | (ClaimRelationship.to_claim_id == claim_id)
        )
        .first()
    )
    if relationship_exists:
        return True

    challenge_link_exists = (
        db.query(ChallengeOutputClaim)
        .filter(ChallengeOutputClaim.claim_id == claim_id)
        .first()
    )
    return challenge_link_exists is not None


def delete_claim(db: Session, claim: Claim) -> None:
    db.delete(claim)
    db.commit()