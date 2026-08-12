import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPk, gen_uuid


class Question(Base, TimestampMixin):
    """Câu hỏi phỏng vấn. criterion_id BẮT BUỘC — mọi câu hỏi sinh ra phải
    trace được về đúng 1 tiêu chí trong competency framework (tránh trôi khỏi rubric).
    is_sensitive_flagged đánh dấu câu hỏi đã bị Sensitive-Attribute Filter chặn hiển thị."""

    __tablename__ = "question"

    id: Mapped[uuid.UUID] = mapped_column(UUIDPk, primary_key=True, default=gen_uuid)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job.id", ondelete="CASCADE"), nullable=False)
    criterion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("criterion.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Giải thích vì sao câu hỏi này đo được tiêu chí đó"
    )
    generated_by: Mapped[str] = mapped_column(String(20), default="agent", comment="agent/human_edited")
    is_sensitive_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    sensitive_flag_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_approved: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="HR phải duyệt trước khi câu hỏi dùng được trong session"
    )