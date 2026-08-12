import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPk, gen_uuid


class Job(Base, TimestampMixin):
    """Một vị trí tuyển dụng. jd_file_path trỏ tới object trong MinIO (file gốc),
    jd_text là kết quả đã parse — HR có thể sửa tay nếu extraction confidence thấp."""

    __tablename__ = "job"

    id: Mapped[uuid.UUID] = mapped_column(UUIDPk, primary_key=True, default=gen_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[str] = mapped_column(String(50), nullable=False, comment="fresher/junior/senior")
    jd_file_path: Mapped[str] = mapped_column(String(512), nullable=False, comment="Object key trong MinIO")
    jd_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    jd_parse_status: Mapped[str] = mapped_column(
        String(20), default="pending", comment="pending/parsed/needs_review"
    )
    framework_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("competency_framework.id"), nullable=False
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)