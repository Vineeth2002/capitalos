from datetime import datetime

from pydantic import BaseModel


class ListingCreate(BaseModel):
    security_id: int
    exchange: str
    symbol: str


class ListingResponse(BaseModel):
    id: int
    security_id: int
    exchange: str
    symbol: str
    created_at: datetime

    class Config:
        from_attributes = True