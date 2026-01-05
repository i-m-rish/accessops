from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.access_request import RequestStatus


class AccessRequestCreate(BaseModel):
    resource: str = Field(min_length=1, max_length=255)
    action: str = Field(min_length=1, max_length=64)
    justification: Optional[str] = None


class AccessRequestOut(BaseModel):
    id: uuid.UUID
    requester_id: uuid.UUID
    resource: str
    action: str
    justification: Optional[str]
    status: RequestStatus
    decided_by: Optional[uuid.UUID]
    decided_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
        