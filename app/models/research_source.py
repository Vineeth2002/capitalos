from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.db.base import Base


class ResearchSource(Base):
    __tablename__ = "research_sources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=True)
    publisher = Column(String, nullable=True)
    source_type = Column(String, nullable=False)
    published_at = Column(DateTime, nullable=True)
    accessed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())