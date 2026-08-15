import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.db import get_db
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

VALID_ROLES = {r.value for r in UserRole}


@router.post("", response_model=UserResponse, status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.hr_admin)),
):
    if payload.role not in VALID_ROLES:
        raise HTTPException(400, f"Role không hợp lệ: {payload.role}")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(409, "Email đã được sử dụng")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.hr_admin)),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(UserRole.hr_admin)),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Người dùng không tồn tại")

    # Chặn tự khoá chính mình - tránh HR Admin duy nhất tự lock-out cả hệ thống.
    if user.id == current.id and payload.is_active is False:
        raise HTTPException(400, "Không thể tự khoá tài khoản của chính mình")

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None:
        if payload.role not in VALID_ROLES:
            raise HTTPException(400, f"Role không hợp lệ: {payload.role}")
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)
    return user