from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func

from app.db.base import Base


class SourceRecord(Base):
    # The originating record within one ingestion run, as identified by the
    # provider. raw_content_reference is a pointer only, never a payload.
    __tablename__ = "source_records"
    __table_args__ = (
        UniqueConstraint("ingestion_run_id", "record_identifier", name="uq_source_record_per_run"),
    )

    id = Column(Integer, primary_key=True, index=True)
    ingestion_run_id = Column(Integer, ForeignKey("ingestion_runs.id"), nullable=False, index=True)
    record_identifier = Column(String, nullable=False)
    raw_content_reference = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())