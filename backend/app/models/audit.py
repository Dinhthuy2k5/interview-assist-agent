import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPk, gen_uuid


class AuditLog(Base):
    """Nhật ký hành động nhạy cảm - KHÔNG dùng TimestampMixin vì log là bất biến
    (không có updated_at, không ai được sửa 1 dòng log đã ghi). actor_id nullable
    vì trường hợp login_failed chưa xác định được actor (sai email/password, có
    thể là bất kỳ ai). Ghi những hành động thật sự cần truy vết - không instrument
    mọi endpoint (sẽ phình quá lớn, khó đọc): đăng nhập, tạo/sửa user, tạo quyết
    định tuyển dụng."""

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUIDPk, primary_key=True, default=gen_uuid)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="login_success/login_failed/user_created/user_updated/decision_created",
    )
    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())