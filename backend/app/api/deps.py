import uuid

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole

# tokenUrl chỉ dùng để Swagger UI hiển thị nút "Authorize" - không ảnh hưởng logic.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(401, "Không xác thực được - vui lòng đăng nhập lại")
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_error
    except JWTError as e:
        raise credentials_error from e

    try:
        user = db.get(User, uuid.UUID(user_id))
    except ValueError:
        raise credentials_error

    if user is None or not user.is_active:
        raise credentials_error
    return user


def require_role(*roles: UserRole):
    """Dependency factory chặn endpoint theo role. Dùng:
    Depends(require_role(UserRole.hr_admin))
    Depends(require_role(UserRole.hr_admin, UserRole.council))"""

    allowed = {r.value for r in roles}

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(403, "Bạn không có quyền thực hiện hành động này")
        return user

    return checker