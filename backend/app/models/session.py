import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPk, gen_uuid


class InterviewSession(Base, TimestampMixin):
    """1 buổi phỏng vấn cho 1 ứng viên ứng tuyển vào 1 Job. status: scheduled ->
    in_progress -> completed. Không lưu điểm/note ở đây - tách riêng InterviewerNote
    vì nhiều interviewer cùng ghi độc lập cho 1 session."""

    __tablename__ = "interview_session"

    id: Mapped[uuid.UUID] = mapped_column(UUIDPk, primary_key=True, default=gen_uuid)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job.id"), nullable=False)
    candidate_name: Mapped[str] = mapped_column(String(255), nullable=False)
    candidate_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="scheduled", comment="scheduled/in_progress/completed"
    )

    interviewers: Mapped[list["SessionInterviewer"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class SessionInterviewer(Base, TimestampMixin):
    """Bảng liên kết N-N: 1 session có nhiều interviewer tham gia độc lập."""

    __tablename__ = "session_interviewer"
    __table_args__ = (UniqueConstraint("session_id", "interviewer_id", name="uq_session_interviewer"),)

    id: Mapped[uuid.UUID] = mapped_column(UUIDPk, primary_key=True, default=gen_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interview_session.id", ondelete="CASCADE"), nullable=False
    )
    interviewer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), nullable=False)

    session: Mapped["InterviewSession"] = relationship(back_populates="interviewers")


class InterviewerNote(Base, TimestampMixin):
    """Note + điểm của 1 interviewer cho 1 criterion trong 1 session. Mỗi interviewer
    CHỈ thấy note của chính mình (đúng nguyên tắc công bằng ở Phân tích ban đầu -
    tránh 1 người ghi note ảnh hưởng người khác trước khi tổng hợp). Unique constraint
    đảm bảo mỗi interviewer chỉ có đúng 1 note cho mỗi criterion trong 1 session -
    PATCH lặp lại là upsert, không tạo bản ghi trùng."""

    __tablename__ = "interviewer_note"
    __table_args__ = (
        UniqueConstraint(
            "session_id", "interviewer_id", "criterion_id", name="uq_note_session_interviewer_criterion"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDPk, primary_key=True, default=gen_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interview_session.id", ondelete="CASCADE"), nullable=False
    )
    interviewer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), nullable=False)
    criterion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("criterion.id"), nullable=False)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="1-5, null nếu chưa chấm")
    note_text: Mapped[str | None] = mapped_column(Text, nullable=True)

class Transcript(Base, TimestampMixin):
    """Bản ghi âm + text đã transcribe cho 1 session. 1 session chỉ có 1 transcript
    (mic ghi cả buổi, dùng chung cho mọi interviewer tham khảo) - unique trên
    session_id để enforce đúng ràng buộc này. retention_expiry set ngay lúc tạo
    theo NFR bảo mật dữ liệu ứng viên (mặc định 180 ngày) - việc xoá tự động khi
    hết hạn là task vận hành riêng (cron/scheduled job), chưa nằm trong scope này."""

    __tablename__ = "transcript"

    id: Mapped[uuid.UUID] = mapped_column(UUIDPk, primary_key=True, default=gen_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interview_session.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    audio_file_path: Mapped[str] = mapped_column(String(512), nullable=False, comment="Object key trong MinIO")
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", comment="pending/processing/completed/failed"
    )
    retention_expiry: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)