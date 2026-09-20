from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func

from app.db.base import Base


class ResearchEvent(Base):
    __tablename__ = "research_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        String, ForeignKey("research_sessions.session_id"), nullable=False, index=True
    )
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())