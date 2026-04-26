from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.access_request import ProvisioningStatus, RequestStatus


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
    provisioning_status: ProvisioningStatus
    decided_by: Optional[uuid.UUID]
    decided_at: Optional[datetime]
    provisioned_at: Optional[datetime]
    provisioning_error: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
