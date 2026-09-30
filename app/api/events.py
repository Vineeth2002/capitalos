from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.event import EventCreate, EventResponse
from app.services import event_service
from app.services.event_service import EventReferenceError

router = APIRouter(tags=["events"])


@router.post("/events", response_model=EventResponse, status_code=201)
def create_event(event_in: EventCreate, db: Session = Depends(get_db)):
    try:
        return event_service.create_event(db, event_in)
    except EventReferenceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/events", response_model=list[EventResponse])
def list_events(
    entity_id: Optional[int] = None,
    security_id: Optional[int] = None,
    listing_id: Optional[int] = None,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return event_service.list_events(
        db,
        entity_id=entity_id,
        security_id=security_id,
        listing_id=listing_id,
        event_type=event_type,
    )


@router.get("/events/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = event_service.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event