import uuid
from enum import Enum

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPk, gen_uuid


class UserRole(str, Enum):
    hr_admin = "hr_admin"
    interviewer = "interviewer"
    council = "council"  # Hội đồng tuyển dụng


class User(Base, TimestampMixin):
    """Tài khoản đăng nhập hệ thống. role quyết định quyền truy cập theo từng
    endpoint (xem app/api/deps.py: require_role). is_active cho phép HR Admin khoá
    tài khoản mà không cần xoá dữ liệu liên quan (job đã tạo, note đã ghi...).
    Không có endpoint tự đăng ký - tài khoản chỉ được tạo bởi HR Admin qua /users."""

    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(UUIDPk, primary_key=True, default=gen_uuid)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, comment="hr_admin/interviewer/council")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)