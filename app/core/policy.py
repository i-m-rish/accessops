from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyResult:
    allowed: bool
    status_code: int | None = None
    detail: str | None = None


def can_access_pending_queue(role: str | None) -> PolicyResult:
    r = (role or "").strip().upper()
    if r in {"APPROVER", "ADMIN"}:
        return PolicyResult(True)
    return PolicyResult(False, 403, "Forbidden")


def can_decide_request(
    *,
    actor_role: str | None,
    actor_id: str,
    requester_id: str,
    current_status: str,
) -> PolicyResult:
    role = (actor_role or "").strip().upper()

    if role not in {"APPROVER", "ADMIN"}:
        return PolicyResult(False, 403, "Forbidden")

    if (current_status or "").strip().upper() != "PENDING":
        return PolicyResult(False, 400, "Request not pending")

    if actor_id == requester_id:
        return PolicyResult(False, 403, "Self-approval is not allowed")

    return PolicyResult(True)
