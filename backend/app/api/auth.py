from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.db import get_db
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import LoginResponse, LogoutRequest, RefreshRequest, RefreshResponse
from app.schemas.user import UserResponse
from app.services.audit import log_action

router = APIRouter(tags=["auth"])


def _issue_tokens(db: Session, user: User) -> tuple[str, str]:
    """Tạo cặp access_token (JWT ngắn hạn, stateless) + refresh_token (random
    string dài hạn, lưu hash trong DB để thu hồi được). Dùng chung cho login và
    refresh (rotation) - không viết lặp lại logic này ở 2 nơi."""
    access_token = create_access_token(str(user.id), user.role)

    raw_refresh = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
        )
    )
    return access_token, raw_refresh


@router.post("/auth/login", response_model=LoginResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not user.is_active or not verify_password(form_data.password, user.password_hash):
        log_action(
            db,
            actor_id=None,
            action="login_failed",
            target_type="user",
            detail=f"email={form_data.username}",
        )
        db.commit()
        raise HTTPException(401, "Email hoặc mật khẩu không đúng")

    access_token, refresh_token = _issue_tokens(db, user)
    log_action(db, actor_id=user.id, action="login_success", target_type="user", target_id=str(user.id))
    db.commit()

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/auth/refresh", response_model=RefreshResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = hash_refresh_token(payload.refresh_token)
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    invalid_error = HTTPException(401, "Refresh token không hợp lệ hoặc đã hết hạn")
    if stored is None:
        raise invalid_error

    if stored.revoked_at is not None:
        # Token đã bị revoke (do logout, hoặc đã dùng để rotate 1 lần trước đó)
        # mà vẫn bị dùng lại - dấu hiệu rõ ràng token có thể đã bị đánh cắp (người
        # dùng thật không bao giờ tự dùng lại token cũ). Revoke TOÀN BỘ refresh
        # token còn sống của user này - buộc đăng nhập lại ở MỌI thiết bị, không
        # chỉ báo lỗi đơn thuần rồi thôi.
        db.query(RefreshToken).filter(
            RefreshToken.user_id == stored.user_id, RefreshToken.revoked_at.is_(None)
        ).update({"revoked_at": datetime.now(UTC)})
        log_action(
            db, actor_id=stored.user_id, action="refresh_token_reuse_detected", target_type="user"
        )
        db.commit()
        raise invalid_error

    # .replace(tzinfo=UTC) nếu DB trả về "naive" datetime (SQLite không giữ
    # timezone qua round-trip, khác Postgres) - không ảnh hưởng gì khi chạy trên
    # Postgres thật (đã tz-aware sẵn, tzinfo is None sẽ luôn False).
    expires_at = stored.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < datetime.now(UTC):
        raise invalid_error

    user = db.get(User, stored.user_id)
    if user is None or not user.is_active:
        raise invalid_error

    # Rotation: revoke token cũ NGAY, cấp cặp token mới - 1 refresh token chỉ
    # dùng được đúng 1 lần.
    stored.revoked_at = datetime.now(UTC)
    access_token, new_refresh_token = _issue_tokens(db, user)
    db.commit()

    return RefreshResponse(access_token=access_token, refresh_token=new_refresh_token, token_type="bearer")


@router.post("/auth/logout", status_code=204)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)):
    """Đây là bước giải quyết đúng vấn đề JWT không lưu trạng thái - access_token
    (JWT) vẫn dùng được tới khi tự hết hạn, KHÔNG thể thu hồi giữa chừng nếu không
    thêm 1 lớp kiểm tra DB cho mỗi request (mất lợi thế tốc độ của JWT). Đổi lại,
    access_token cố tình để hạn NGẮN (30 phút - xem settings.jwt_expire_minutes),
    còn logout THẬT SỰ có hiệu lực ở refresh_token: revoke ngay, user không refresh
    được access_token mới nữa - chỉ còn dùng được access_token cũ (nếu có) cho tới
    khi nó tự hết hạn, khung thời gian ngắn, chấp nhận được."""
    token_hash = hash_refresh_token(payload.refresh_token)
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if stored is not None and stored.revoked_at is None:
        stored.revoked_at = datetime.now(UTC)
        log_action(
            db, actor_id=stored.user_id, action="logout", target_type="user", target_id=str(stored.user_id)
        )
        db.commit()
    # Không raise lỗi nếu token không tồn tại/đã revoke - logout nên "idempotent"
    # (gọi lại nhiều lần không sao), và không lộ thông tin token có tồn tại hay
    # không cho client (tránh dò được refresh token nào còn "sống").


@router.get("/auth/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user