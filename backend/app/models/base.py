import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class cho toàn bộ model. Mọi bảng dùng UUID làm khóa chính
    (an toàn hơn incremental ID khi expose qua API — tránh lộ thông tin số lượng record)."""

    pass


class TimestampMixin:
    """Mixin thêm created_at/updated_at cho mọi bảng cần audit trail."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


def gen_uuid() -> uuid.UUID:
    return uuid.uuid4()


UUIDPk = UUID(as_uuid=True)