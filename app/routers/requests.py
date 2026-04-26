from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core import policy
from app.core.rbac import get_current_claims, require_role
from app.db.deps import get_db
from app.models.access_request import AccessRequest, ProvisioningStatus, RequestStatus
from app.schemas.access_request import AccessRequestCreate, AccessRequestOut
from app.services import audit_service

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
        provisioning_status=ProvisioningStatus.NOT_STARTED,
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
    role = (claims.get("role") or "").strip().upper()
    user_id = uuid.UUID(str(claims["sub"]))

    q = db.query(AccessRequest)
    if role == "REQUESTER":
        q = q.filter(AccessRequest.requester_id == user_id)

    return q.order_by(AccessRequest.created_at.desc()).all()


@router.get("/pending", response_model=list[AccessRequestOut])
def list_pending_requests(
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_claims),
) -> list[AccessRequest]:
    res = policy.can_access_pending_queue(claims.get("role"))
    if not res.allowed:
        raise HTTPException(status_code=res.status_code or 403, detail=res.detail or "Forbidden")

    return (
        db.query(AccessRequest)
        .filter(AccessRequest.status == RequestStatus.PENDING)
        .order_by(AccessRequest.created_at.desc())
        .all()
    )


def _get_request(db: Session, request_id: uuid.UUID) -> AccessRequest:
    req = db.get(AccessRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req


@router.patch("/{request_id}/approve", response_model=AccessRequestOut)
def approve_request(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_claims),
) -> AccessRequest:
    req = _get_request(db, request_id)

    actor_id = str(claims["sub"])
    requester_id = str(req.requester_id)
    current_status = req.status.value if hasattr(req.status, "value") else str(req.status)

    res = policy.can_decide_request(
        actor_role=claims.get("role"),
        actor_id=actor_id,
        requester_id=requester_id,
        current_status=current_status,
    )
    if not res.allowed:
        raise HTTPException(status_code=res.status_code or 403, detail=res.detail or "Forbidden")

    req.status = RequestStatus.APPROVED
    req.provisioning_status = ProvisioningStatus.QUEUED
    req.decided_by = uuid.UUID(actor_id)
    req.decided_at = datetime.now(timezone.utc)

    audit_service.emit(
        db,
        actor_id=req.decided_by,
        action="access_request.approved",
        entity_type="access_request",
        entity_id=req.id,
        details={
            "requester_id": str(req.requester_id),
            "resource": req.resource,
            "action": req.action,
            "previous_status": "PENDING",
            "new_status": "APPROVED",
            "previous_provisioning_status": "NOT_STARTED",
            "new_provisioning_status": "QUEUED",
        },
    )

    db.commit()
    db.refresh(req)
    return req


@router.patch("/{request_id}/reject", response_model=AccessRequestOut)
def reject_request(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_claims),
) -> AccessRequest:
    req = _get_request(db, request_id)

    actor_id = str(claims["sub"])
    requester_id = str(req.requester_id)
    current_status = req.status.value if hasattr(req.status, "value") else str(req.status)

    res = policy.can_decide_request(
        actor_role=claims.get("role"),
        actor_id=actor_id,
        requester_id=requester_id,
        current_status=current_status,
    )
    if not res.allowed:
        raise HTTPException(status_code=res.status_code or 403, detail=res.detail or "Forbidden")

    req.status = RequestStatus.REJECTED
    req.provisioning_status = ProvisioningStatus.NOT_STARTED
    req.decided_by = uuid.UUID(actor_id)
    req.decided_at = datetime.now(timezone.utc)

    audit_service.emit(
        db,
        actor_id=req.decided_by,
        action="access_request.rejected",
        entity_type="access_request",
        entity_id=req.id,
        details={
            "requester_id": str(req.requester_id),
            "resource": req.resource,
            "action": req.action,
            "previous_status": "PENDING",
            "new_status": "REJECTED",
            "provisioning_status": "NOT_STARTED",
        },
    )

    db.commit()
    db.refresh(req)
    return req


@router.patch("/{request_id}/provision", response_model=AccessRequestOut)
def mark_provisioned(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    claims: dict = Depends(require_role("ADMIN")),
) -> AccessRequest:
    req = _get_request(db, request_id)
    if req.status != RequestStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Only approved requests can be provisioned")
    if req.provisioning_status == ProvisioningStatus.PROVISIONED:
        raise HTTPException(status_code=400, detail="Request already provisioned")

    req.provisioning_status = ProvisioningStatus.PROVISIONED
    req.provisioned_at = datetime.now(timezone.utc)
    req.provisioning_error = None

    audit_service.emit(
        db,
        actor_id=uuid.UUID(str(claims["sub"])),
        action="access_request.provisioned",
        entity_type="access_request",
        entity_id=req.id,
        details={
            "requester_id": str(req.requester_id),
            "resource": req.resource,
            "action": req.action,
            "new_provisioning_status": "PROVISIONED",
        },
    )

    db.commit()
    db.refresh(req)
    return req
