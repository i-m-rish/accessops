import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.rbac import require_role
from app.db.deps import get_db
from app.models.user import User
from app.schemas.admin import UserOut, UserRoleUpdate

router = APIRouter(prefix="/admin", tags=["admin"])

ALLOWED_ROLES = {"REQUESTER", "APPROVER", "ADMIN"}


@router.patch("/users/{user_id}/role", response_model=UserOut)
def update_user_role(
    user_id: uuid.UUID,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    claims: dict = Depends(require_role("ADMIN")),
) -> UserOut:
    role = (payload.role or "").strip().upper()
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = role
    db.commit()
    db.refresh(user)

    return UserOut(id=str(user.id), email=user.email, role=user.role)
