import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPk, gen_uuid


class RefreshToken(Base, TimestampMixin):
    """Refresh token cho phép cấp lại access_token mới mà không cần đăng nhập lại,
    đồng thời là cơ chế DUY NHẤT thực sự "đăng xuất" được - access_token (JWT) tự
    thân không lưu trạng thái, không thể thu hồi giữa chừng trước khi hết hạn.

    Lưu HASH (sha256), không lưu token gốc - giống nguyên tắc password_hash: nếu
    DB rò rỉ, refresh token trong đó vẫn không dùng được trực tiếp.

    revoked_at khác None nghĩa là token đã bị vô hiệu hoá (do logout, hoặc bị
    "xoay vòng" - mỗi lần refresh thành công sẽ revoke token cũ và cấp token mới,
    hạn chế 1 refresh token bị lộ có thể dùng lại nhiều lần)."""

    __tablename__ = "refresh_token"

    id: Mapped[uuid.UUID] = mapped_column(UUIDPk, primary_key=True, default=gen_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)