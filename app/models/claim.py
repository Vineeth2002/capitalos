from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    research_case_id: Mapped[int] = mapped_column(ForeignKey("research_cases.id"), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(ForeignKey("entities.id"), nullable=True)
    statement: Mapped[str] = mapped_column(String, nullable=False)
    temporal_orientation: Mapped[str] = mapped_column(String, nullable=False)
    epistemic_role: Mapped[str] = mapped_column(String, nullable=False)
    shape: Mapped[str] = mapped_column(String, nullable=False)
    confidence_band: Mapped[str | None] = mapped_column(String, nullable=True)
    lifecycle_status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    lens: Mapped[str | None] = mapped_column(String, nullable=True)
    origin: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)