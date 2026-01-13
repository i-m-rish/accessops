from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session


def emit(
    db: Session,
    *,
    actor_id,
    action: str,
    entity_type: str,
    entity_id,
    details: dict | None = None,
) -> None:
    db.execute(
        text(
            """
            insert into audit_events (id, actor_id, action, entity_type, entity_id, details, created_at)
            values (:id, :actor_id, :action, :entity_type, :entity_id, CAST(:details AS jsonb), :created_at)
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "actor_id": str(actor_id) if actor_id is not None else None,
            "action": action,
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "details": json.dumps(details or {}),
            "created_at": datetime.now(timezone.utc),
        },
    )
