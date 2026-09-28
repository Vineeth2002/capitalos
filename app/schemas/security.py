from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator


class SecurityCreate(BaseModel):
    issuer_entity_id: int
    identifier_type: Optional[str] = None
    identifier: Optional[str] = None

    @model_validator(mode="after")
    def identifier_and_type_together(self):
        if (self.identifier_type is None) != (self.identifier is None):
            raise ValueError("identifier_type and identifier must be provided together")
        return self


class SecurityResponse(BaseModel):
    id: int
    issuer_entity_id: int
    identifier_type: Optional[str]
    identifier: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True