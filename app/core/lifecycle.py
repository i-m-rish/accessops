from __future__ import annotations

from enum import StrEnum
from typing import Final


class RequestStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


# Allowed state transitions (source of truth)
ALLOWED_TRANSITIONS: Final[dict[RequestStatus, set[RequestStatus]]] = {
    RequestStatus.PENDING: {RequestStatus.APPROVED, RequestStatus.REJECTED, RequestStatus.CANCELLED},
    RequestStatus.APPROVED: set(),
    RequestStatus.REJECTED: set(),
    RequestStatus.CANCELLED: set(),
}


def can_transition(from_status: RequestStatus, to_status: RequestStatus) -> bool:
    return to_status in ALLOWED_TRANSITIONS.get(from_status, set())
