from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.fact_classification import (
    FactClassificationCreate,
    FactClassificationResponse,
)
from app.services import fact_classification_service
from app.services.fact_classification_service import ClassificationError

router = APIRouter(tags=["fact-classifications"])


@router.post(
    "/fact-classifications", response_model=FactClassificationResponse, status_code=201
)
def create_fact_classification(
    classification_in: FactClassificationCreate, db: Session = Depends(get_db)
):
    try:
        return fact_classification_service.create_classification(db, classification_in)
    except ClassificationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/fact-classifications", response_model=list[FactClassificationResponse])
def list_fact_classifications(
    applies_to: Optional[str] = None, db: Session = Depends(get_db)
):
    return fact_classification_service.list_classifications(db, applies_to=applies_to)