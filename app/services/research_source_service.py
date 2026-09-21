from app.models.claim_source import ClaimSource
from app.models.research_source import ResearchSource


def create_source(db, source_in):
    source = ResearchSource(
        title=source_in.title,
        url=source_in.url,
        publisher=source_in.publisher,
        source_type=source_in.source_type.value,
        published_at=source_in.published_at,
        accessed_at=source_in.accessed_at,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def get_source(db, source_id):
    return db.get(ResearchSource, source_id)


def list_sources(db):
    return db.query(ResearchSource).order_by(ResearchSource.created_at.asc()).all()


def claim_source_exists(db, claim_id, source_id):
    return (
        db.query(ClaimSource)
        .filter(ClaimSource.claim_id == claim_id, ClaimSource.source_id == source_id)
        .first()
        is not None
    )


def attach_source_to_claim(db, claim_id, attach_in):
    claim_source = ClaimSource(
        claim_id=claim_id,
        source_id=attach_in.source_id,
        relationship_type=attach_in.relationship_type.value,
        excerpt=attach_in.excerpt,
    )
    db.add(claim_source)
    db.commit()
    db.refresh(claim_source)
    return claim_source


def list_sources_for_claim(db, claim_id):
    return (
        db.query(ClaimSource)
        .filter(ClaimSource.claim_id == claim_id)
        .order_by(ClaimSource.created_at.asc())
        .all()
    )


def list_claims_for_source(db, source_id):
    return (
        db.query(ClaimSource)
        .filter(ClaimSource.source_id == source_id)
        .order_by(ClaimSource.created_at.asc())
        .all()
    )


def get_claim_source(db, claim_id, source_id):
    return (
        db.query(ClaimSource)
        .filter(ClaimSource.claim_id == claim_id, ClaimSource.source_id == source_id)
        .first()
    )


def detach_source_from_claim(db, claim_source):
    db.delete(claim_source)
    db.commit()