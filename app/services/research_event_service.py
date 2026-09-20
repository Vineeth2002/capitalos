from app.models.research_session import ResearchSession
from app.models.research_event import ResearchEvent


def get_or_create_session(db, session_id):
    session = (
        db.query(ResearchSession)
        .filter(ResearchSession.session_id == session_id)
        .first()
    )
    if session:
        return session

    session = ResearchSession(session_id=session_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def create_event(db, event_in):
    get_or_create_session(db, event_in.session_id)

    event = ResearchEvent(
        session_id=event_in.session_id,
        event_type=event_in.event_type,
        payload=event_in.payload,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_events_for_session(db, session_id):
    return (
        db.query(ResearchEvent)
        .filter(ResearchEvent.session_id == session_id)
        .order_by(ResearchEvent.created_at.asc())
        .all()
    )


def session_exists(db, session_id):
    return (
        db.query(ResearchSession)
        .filter(ResearchSession.session_id == session_id)
        .first()
        is not None
    )