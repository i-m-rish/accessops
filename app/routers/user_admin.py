import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.rbac import require_role
from app.db.deps import get_db
from app.models.user import User
from app.schemas.admin import UserOut, UserRoleUpdate

router = APIRouter(prefix="/user-admin", tags=["user-admin"])

ROLE_NAMES = {"REQUESTER", "APPROVER", "ADMIN"}


@router.patch("/users/{user_id}/role", response_model=UserOut)
def set_user_role(
    user_id: uuid.UUID,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    _claims: dict = Depends(require_role("ADMIN")),
) -> UserOut:
    role_name = payload.role.strip().upper()
    if role_name not in ROLE_NAMES:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = role_name
    db.commit()
    db.refresh(user)

    return UserOut(id=str(user.id), email=user.email, role=user.role)
