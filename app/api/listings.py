from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.listing import ListingCreate, ListingResponse
from app.services import security_service
from app.services.security_service import IdentityError

router = APIRouter(tags=["listings"])


@router.post("/listings", response_model=ListingResponse, status_code=201)
def create_listing(listing_in: ListingCreate, db: Session = Depends(get_db)):
    try:
        return security_service.create_listing(db, listing_in)
    except IdentityError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/listings", response_model=list[ListingResponse])
def list_listings(db: Session = Depends(get_db)):
    return security_service.list_listings(db)


@router.get("/listings/{listing_id}", response_model=ListingResponse)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = security_service.get_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing