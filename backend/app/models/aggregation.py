import uuid

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPk, gen_uuid


class AggregationReport(Base, TimestampMixin):
    """Kết quả tổng hợp đánh giá đa người phỏng vấn cho 1 session - THUẦN ADVISORY,
    không phải quyết định cuối (xem ADR 0001). Service tạo bảng này KHÔNG có quyền
    ghi vào bảng Decision (Sprint 6) - tách biệt hoàn toàn ở tầng model lẫn service.

    Khác với Transcript (audio gốc, không cho ghi đè - coi như bằng chứng), report
    này là dữ liệu TÍNH TOÁN LẠI ĐƯỢC từ InterviewerNote - upsert tự do khi HR
    chạy lại (có note mới, hoặc muốn tính lại), unique constraint đủ để enforce
    1 report/session mới nhất."""

    __tablename__ = "aggregation_report"

    id: Mapped[uuid.UUID] = mapped_column(UUIDPk, primary_key=True, default=gen_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interview_session.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    per_criterion_summary: Mapped[list] = mapped_column(
        JSON, nullable=False, comment="List[{criterion_id, criterion_name, scores, average, "
        "has_conflict, conflict_type, semantic_note, missing_interviewer_count}]"
    )
    overall_score: Mapped[float | None] = mapped_column(
        Numeric(3, 2), nullable=True, comment="Điểm trung bình có trọng số, null nếu chưa có note nào"
    )
    overall_recommendation: Mapped[str] = mapped_column(
        String(50), comment="Đề xuất tuyển / Cần thảo luận thêm / Không đề xuất - Chỉ tư vấn"
    )
    rationale_trace: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Narrative giải thích - bắt buộc, không được chỉ trả số trần trụi"
    )