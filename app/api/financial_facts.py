from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entity import Entity
from app.models.research_source import ResearchSource
from app.schemas.financial_fact import FinancialFactCreate, FinancialFactResponse
from app.services import financial_fact_service

router = APIRouter(tags=["financial-facts"])


@router.post("/financial-facts", response_model=FinancialFactResponse, status_code=201)
def create_financial_fact(
    fact_in: FinancialFactCreate, db: Session = Depends(get_db)
):
    entity = db.get(Entity, fact_in.entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    if fact_in.source_id is not None:
        source = db.get(ResearchSource, fact_in.source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

    return financial_fact_service.create_fact(db, fact_in)


@router.get("/financial-facts", response_model=list[FinancialFactResponse])
def list_financial_facts(
    entity_id: Optional[int] = None,
    fact_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return financial_fact_service.list_facts(db, entity_id=entity_id, fact_type=fact_type)


@router.get("/financial-facts/{fact_id}", response_model=FinancialFactResponse)
def get_financial_fact(fact_id: int, db: Session = Depends(get_db)):
    fact = financial_fact_service.get_fact(db, fact_id)
    if not fact:
        raise HTTPException(status_code=404, detail="Financial fact not found")
    return fact