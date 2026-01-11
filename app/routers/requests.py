from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.rbac import get_current_claims, require_role
from app.db.deps import get_db
from app.models.access_request import AccessRequest, RequestStatus
from app.schemas.access_request import AccessRequestCreate, AccessRequestOut

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post("", response_model=AccessRequestOut, status_code=status.HTTP_201_CREATED)
def create_request(
    payload: AccessRequestCreate,
    db: Session = Depends(get_db),
    claims: dict = Depends(require_role("REQUESTER", "APPROVER", "ADMIN")),
) -> AccessRequest:
    req = AccessRequest(
        requester_id=uuid.UUID(str(claims["sub"])),
        resource=payload.resource,
        action=payload.action,
        justification=payload.justification,
        status=RequestStatus.PENDING,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@router.get("", response_model=list[AccessRequestOut])
def list_requests(
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_claims),
) -> list[AccessRequest]:
    role = (claims.get("role") or "").strip()
    user_id = uuid.UUID(str(claims["sub"]))

    q = db.query(AccessRequest)

    if role == "REQUESTER":
        q = q.filter(AccessRequest.requester_id == user_id)

    return q.order_by(AccessRequest.created_at.desc()).all()


# 🔒 REQUIRED FOR WORKFLOW TESTS
@router.get("/pending", response_model=list[AccessRequestOut])
def list_pending_requests(
    db: Session = Depends(get_db),
    claims: dict = Depends(require_role("APPROVER", "ADMIN")),
) -> list[AccessRequest]:
    return (
        db.query(AccessRequest)
        .filter(AccessRequest.status == RequestStatus.PENDING)
        .order_by(AccessRequest.created_at.desc())
        .all()
    )


def _get_pending_request(db: Session, request_id: uuid.UUID) -> AccessRequest:
    req = db.get(AccessRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request not pending")
    return req


@router.patch("/{request_id}/approve", response_model=AccessRequestOut)
def approve_request(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    claims: dict = Depends(require_role("APPROVER", "ADMIN")),
) -> AccessRequest:
    req = _get_pending_request(db, request_id)
    req.status = RequestStatus.APPROVED
    req.decided_by = uuid.UUID(str(claims["sub"]))
    req.decided_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(req)
    return req


@router.patch("/{request_id}/reject", response_model=AccessRequestOut)
def reject_request(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    claims: dict = Depends(require_role("APPROVER", "ADMIN")),
) -> AccessRequest:
    req = _get_pending_request(db, request_id)
    req.status = RequestStatus.REJECTED
    req.decided_by = uuid.UUID(str(claims["sub"]))
    req.decided_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(req)
    return req
