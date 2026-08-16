import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPk, gen_uuid


class Job(Base, TimestampMixin):
    """Một vị trí tuyển dụng. jd_file_path trỏ tới object trong MinIO (file gốc),
    jd_text là kết quả đã parse — HR có thể sửa tay nếu extraction confidence thấp.

    application_deadline/is_closed quyết định trạng thái "đang tuyển"/"đã đóng" -
    trạng thái này KHÔNG lưu thành cột riêng, tính động ở tầng schema (xem
    JobResponse.status) để tránh lệch dữ liệu khi job qua hạn mà không có cron
    job nào chạy cập nhật."""

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
    application_deadline: Mapped[date | None] = mapped_column(
        Date, nullable=True, comment="Hạn nộp hồ sơ - null nghĩa là không giới hạn"
    )
    is_closed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="HR đóng tuyển tay, trước hoặc sau hạn"
    )