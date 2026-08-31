from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.auth import LoginResponse
from app.schemas.user import UserResponse
from app.services.audit import log_action

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=LoginResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm dùng field "username" theo chuẩn OAuth2 - ở đây
    # chứa email. Giữ chuẩn này để Swagger UI "Authorize" hoạt động luôn không
    # cần cấu hình thêm.
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not user.is_active or not verify_password(form_data.password, user.password_hash):
        # actor_id=None vì chưa xác định được ai (có thể là bất kỳ ai gõ sai) -
        # detail chỉ ghi email thử đăng nhập, KHÔNG ghi password dù đúng hay sai.
        log_action(
            db,
            actor_id=None,
            action="login_failed",
            target_type="user",
            detail=f"email={form_data.username}",
        )
        db.commit()
        raise HTTPException(401, "Email hoặc mật khẩu không đúng")

    token = create_access_token(str(user.id), user.role)
    log_action(db, actor_id=user.id, action="login_success", target_type="user", target_id=str(user.id))
    db.commit()

    return LoginResponse(access_token=token, token_type="bearer", user=UserResponse.model_validate(user))


@router.get("/auth/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user