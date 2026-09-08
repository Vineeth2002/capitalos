from app.models.claim import Claim
from app.models.entity import Entity
from app.models.research_case import ResearchCase


def confirm_reasoning(db, payload):
    # Atomicity: nothing is committed until every claim (and the entity
    # reference check for each) has succeeded. flush() pushes SQL within
    # the open transaction so we can get generated IDs, but a rollback()
    # before commit() discards everything, including the ResearchCase.
    if payload.entity_id is not None:
        entity = db.get(Entity, payload.entity_id)
        if not entity:
            raise ValueError("Entity not found: " + str(payload.entity_id))

    research_case = ResearchCase(
        entity_id=payload.entity_id,
        title=payload.title,
        description=payload.description,
        status="active",
    )
    db.add(research_case)
    db.flush()

    created_claims = []
    for claim_in in payload.claims:
        if claim_in.entity_id is not None:
            entity = db.get(Entity, claim_in.entity_id)
            if not entity:
                raise ValueError("Entity not found: " + str(claim_in.entity_id))

        claim = Claim(
            research_case_id=research_case.id,
            entity_id=claim_in.entity_id,
            statement=claim_in.statement,
            temporal_orientation=claim_in.temporal_orientation,
            epistemic_role=claim_in.epistemic_role,
            shape=claim_in.shape,
            confidence_band=claim_in.confidence_band,
            lifecycle_status=claim_in.lifecycle_status,
            lens=claim_in.lens,
            origin=claim_in.origin,
        )
        db.add(claim)
        created_claims.append(claim)

    db.commit()
    db.refresh(research_case)
    for claim in created_claims:
        db.refresh(claim)

    return research_case, created_claims