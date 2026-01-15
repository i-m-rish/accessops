import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.db.base import Base
from sqlalchemy.types import JSON


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)

    details = Column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=False,
        server_default=text("'{}'")
    )

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
