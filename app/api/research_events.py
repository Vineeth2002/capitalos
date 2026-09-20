from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.research_event import ResearchEventCreate, ResearchEventResponse
from app.services import research_event_service

router = APIRouter(tags=["research-events"])


@router.post("/research-events", response_model=ResearchEventResponse, status_code=201)
def create_research_event(
    event_in: ResearchEventCreate, db: Session = Depends(get_db)
):
    return research_event_service.create_event(db, event_in)


@router.get("/research-events", response_model=list[ResearchEventResponse])
def list_research_events(session_id: str, db: Session = Depends(get_db)):
    if not research_event_service.session_exists(db, session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return research_event_service.list_events_for_session(db, session_id)