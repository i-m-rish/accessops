from __future__ import annotations

from enum import StrEnum
from typing import Final


class Role(StrEnum):
    REQUESTER = "REQUESTER"
    APPROVER = "APPROVER"
    ADMIN = "ADMIN"


# Use these action names consistently in routers/tests.
ACTIONS: Final[set[str]] = {
    "request:create",
    "request:read:self",
    "request:cancel:self",
    "request:read:any",
    "request:approve",
    "request:reject",
    "request:override",
}


ROLE_ACTIONS: Final[dict[Role, set[str]]] = {
    Role.REQUESTER: {"request:create", "request:read:self", "request:cancel:self"},
    Role.APPROVER: {"request:read:any", "request:approve", "request:reject"},
    Role.ADMIN: {"request:read:any", "request:approve", "request:reject", "request:override"},
}


def has_action(role: str | None, action: str) -> bool:
    if not role:
        return False
    try:
        r = Role(role)
    except ValueError:
        return False
    return action in ROLE_ACTIONS.get(r, set())
