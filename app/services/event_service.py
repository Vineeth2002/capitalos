from datetime import timezone

from app.models.entity import Entity
from app.models.event import Event
from app.models.listing import Listing
from app.models.research_source import ResearchSource
from app.models.security import Security
from app.models.source_record import SourceRecord


class EventReferenceError(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _naive_utc(value):
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def validate_references(db, event_in):
    if event_in.entity_id is not None and not db.get(Entity, event_in.entity_id):
        raise EventReferenceError(404, "Entity not found")
    if event_in.security_id is not None and not db.get(Security, event_in.security_id):
        raise EventReferenceError(404, "Security not found")
    if event_in.listing_id is not None and not db.get(Listing, event_in.listing_id):
        raise EventReferenceError(404, "Listing not found")
    if event_in.source_id is not None and not db.get(ResearchSource, event_in.source_id):
        raise EventReferenceError(404, "Source not found")
    if event_in.source_record_id is not None and not db.get(
        SourceRecord, event_in.source_record_id
    ):
        raise EventReferenceError(404, "Source record not found")

    if event_in.supersedes_id is not None:
        target = db.get(Event, event_in.supersedes_id)
        if not target:
            raise EventReferenceError(404, "Event to supersede not found")
        target_subject = (target.entity_id, target.security_id, target.listing_id)
        new_subject = (event_in.entity_id, event_in.security_id, event_in.listing_id)
        if target_subject != new_subject:
            raise EventReferenceError(422, "A correction must have the same subject")
        if target.event_type != event_in.event_type:
            raise EventReferenceError(422, "A correction must have the same event_type")
        already = (
            db.query(Event)
            .filter(Event.supersedes_id == target.id)
            .first()
        )
        if already:
            raise EventReferenceError(409, "This event has already been superseded")


def create_event(db, event_in):
    validate_references(db, event_in)

    event = Event(
        entity_id=event_in.entity_id,
        security_id=event_in.security_id,
        listing_id=event_in.listing_id,
        event_type=event_in.event_type,
        description=event_in.description,
        event_date=event_in.event_date,
        published_at=_naive_utc(event_in.published_at),
        source_id=event_in.source_id,
        source_record_id=event_in.source_record_id,
        supersedes_id=event_in.supersedes_id,
        supersession_reason=event_in.supersession_reason,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_event(db, event_id):
    return db.get(Event, event_id)


def list_events(db, entity_id=None, security_id=None, listing_id=None, event_type=None):
    query = db.query(Event)
    if entity_id is not None:
        query = query.filter(Event.entity_id == entity_id)
    if security_id is not None:
        query = query.filter(Event.security_id == security_id)
    if listing_id is not None:
        query = query.filter(Event.listing_id == listing_id)
    if event_type is not None:
        query = query.filter(Event.event_type == event_type)
    return query.order_by(Event.id.asc()).all()