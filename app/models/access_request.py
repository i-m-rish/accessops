import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ProvisioningStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    QUEUED = "QUEUED"
    PROVISIONED = "PROVISIONED"
    FAILED = "FAILED"


class AccessRequest(Base):
    __tablename__ = "access_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    requester_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    resource: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[RequestStatus] = mapped_column(Enum(RequestStatus, name="request_status"), nullable=False, default=RequestStatus.PENDING)
    provisioning_status: Mapped[ProvisioningStatus] = mapped_column(
        Enum(ProvisioningStatus, name="provisioning_status"),
        nullable=False,
        default=ProvisioningStatus.NOT_STARTED,
        server_default=ProvisioningStatus.NOT_STARTED.value,
    )

    decided_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provisioned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provisioning_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    requester = relationship("User", foreign_keys=[requester_id], passive_deletes=True)
    decider = relationship("User", foreign_keys=[decided_by], passive_deletes=True)
