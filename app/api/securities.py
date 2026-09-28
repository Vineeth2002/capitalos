from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.security import SecurityCreate, SecurityResponse
from app.services import security_service
from app.services.security_service import IdentityError

router = APIRouter(tags=["securities"])


@router.post("/securities", response_model=SecurityResponse, status_code=201)
def create_security(security_in: SecurityCreate, db: Session = Depends(get_db)):
    try:
        return security_service.create_security(db, security_in)
    except IdentityError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/securities", response_model=list[SecurityResponse])
def list_securities(db: Session = Depends(get_db)):
    return security_service.list_securities(db)


@router.get("/securities/{security_id}", response_model=SecurityResponse)
def get_security(security_id: int, db: Session = Depends(get_db)):
    security = security_service.get_security(db, security_id)
    if not security:
        raise HTTPException(status_code=404, detail="Security not found")
    return security