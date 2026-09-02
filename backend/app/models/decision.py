import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPk, gen_uuid


class SessionDecision(Base, TimestampMixin):
    """Quyết định tuyển dụng CUỐI CÙNG do Hội đồng ghi - authoritative, khác hẳn
    AggregationReport (chỉ advisory, xem ADR 0001: Aggregation Service tuyệt đối
    không được ghi vào bảng này).

    APPEND-ONLY: mỗi lần Council quyết định (hoặc đổi ý sau khi có thêm thông tin)
    tạo 1 dòng MỚI, không sửa/xoá dòng cũ - bản thân bảng này chính là audit trail
    cho quyết định tuyển dụng, không cho sửa lịch sử. "Quyết định hiện tại" của 1
    session = dòng mới nhất theo created_at.

    decided_by hiện TÊN THẬT (không ẩn danh như InterviewerNote.interviewer_id) -
    ẩn danh note là để tránh thiên vị lúc đánh giá độc lập, nhưng quyết định cuối
    là hành vi có trách nhiệm cá nhân, cần truy vết được ai quyết định."""

    __tablename__ = "session_decision"

    id: Mapped[uuid.UUID] = mapped_column(UUIDPk, primary_key=True, default=gen_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interview_session.id", ondelete="CASCADE"), nullable=False
    )
    decided_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False, comment="hired/rejected/on_hold")
    rationale: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Lý do quyết định - bắt buộc, không được để trống"
    )