from sqlalchemy.orm import Session

from app.models.claim_relationship import ClaimRelationship
from app.schemas.claim_relationship import ClaimRelationshipCreate


def create_relationship(
    db: Session, from_claim_id: int, relationship_in: ClaimRelationshipCreate
) -> ClaimRelationship:
    relationship = ClaimRelationship(
        from_claim_id=from_claim_id, **relationship_in.model_dump()
    )
    db.add(relationship)
    db.commit()
    db.refresh(relationship)
    return relationship


def list_claim_relationships(db: Session, claim_id: int) -> list[ClaimRelationship]:
    return (
        db.query(ClaimRelationship)
        .filter(ClaimRelationship.from_claim_id == claim_id)
        .all()
    )