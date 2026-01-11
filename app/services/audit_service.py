from sqlalchemy.orm import Session

from app.models.audit import AuditEvent


def emit(
    db: Session,
    *,
    actor_id,
    action: str,
    entity_type: str,
    entity_id,
    details: dict | None,
) -> AuditEvent:
    evt = AuditEvent(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
    )
    db.add(evt)
    return evt
