from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class ResearchEventCreate(BaseModel):
    session_id: str
    event_type: str
    payload: Optional[Any] = None


class ResearchEventResponse(BaseModel):
    id: int
    session_id: str
    event_type: str
    payload: Optional[Any]
    created_at: datetime

    class Config:
        from_attributes = True