from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.time_utils import to_naive_utc
from app.db.session import get_db
from app.models.entity import Entity
from app.models.research_case import ResearchCase
from app.schemas.research_case import ResearchCaseCreate, ResearchCaseUpdate, ResearchCaseResponse

router = APIRouter(prefix="/research-cases", tags=["research-cases"])


@router.post("", response_model=ResearchCaseResponse)
def create_research_case(case_in: ResearchCaseCreate, db: Session = Depends(get_db)):
    if case_in.entity_id is not None:
        entity = db.get(Entity, case_in.entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
    data = case_in.model_dump()
    data["knowledge_cutoff_at"] = to_naive_utc(data.get("knowledge_cutoff_at"))
    case = ResearchCase(**data)
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.get("", response_model=list[ResearchCaseResponse])
def list_research_cases(db: Session = Depends(get_db)):
    return db.query(ResearchCase).all()


@router.get("/{case_id}", response_model=ResearchCaseResponse)
def get_research_case(case_id: int, db: Session = Depends(get_db)):
    case = db.get(ResearchCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Research case not found")
    return case


@router.patch("/{case_id}", response_model=ResearchCaseResponse)
def update_research_case(case_id: int, case_in: ResearchCaseUpdate, db: Session = Depends(get_db)):
    case = db.get(ResearchCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Research case not found")
    if case_in.entity_id is not None:
        entity = db.get(Entity, case_in.entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
    update_data = case_in.model_dump(exclude_unset=True)

    # knowledge_cutoff_at is set at creation only. Omitted, or equal to the
    # stored instant, is a no-op. Anything else is rejected, including
    # NULL -> timestamp and timestamp -> NULL. This runs before any field is
    # applied, so a rejected request changes nothing.
    if "knowledge_cutoff_at" in update_data:
        incoming = to_naive_utc(update_data.pop("knowledge_cutoff_at"))
        existing = to_naive_utc(case.knowledge_cutoff_at)
        if incoming != existing:
            raise HTTPException(
                status_code=422,
                detail=(
                    "knowledge_cutoff_at can only be set when the research "
                    "case is created and cannot be changed afterwards"
                ),
            )

    for field, value in update_data.items():
        setattr(case, field, value)
    db.add(case)
    db.commit()
    db.refresh(case)
    return case