from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.financial_fact import FinancialFactCreate, FinancialFactResponse
from app.services import financial_fact_service
from app.services.financial_fact_service import FactReferenceError

router = APIRouter(tags=["financial-facts"])


@router.post("/financial-facts", response_model=FinancialFactResponse, status_code=201)
def create_financial_fact(fact_in: FinancialFactCreate, db: Session = Depends(get_db)):
    try:
        return financial_fact_service.create_fact(db, fact_in)
    except FactReferenceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/financial-facts", response_model=list[FinancialFactResponse])
def list_financial_facts(
    entity_id: Optional[int] = None,
    security_id: Optional[int] = None,
    listing_id: Optional[int] = None,
    fact_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return financial_fact_service.list_facts(
        db,
        entity_id=entity_id,
        security_id=security_id,
        listing_id=listing_id,
        fact_type=fact_type,
    )


@router.get("/financial-facts/{fact_id}", response_model=FinancialFactResponse)
def get_financial_fact(fact_id: int, db: Session = Depends(get_db)):
    fact = financial_fact_service.get_fact(db, fact_id)
    if not fact:
        raise HTTPException(status_code=404, detail="Financial fact not found")
    return fact