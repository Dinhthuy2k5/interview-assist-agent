import uuid

from pydantic import BaseModel, ConfigDict


class CriterionSummary(BaseModel):
    criterion_id: uuid.UUID
    criterion_name: str
    scores: list[int]
    average: float | None
    has_conflict: bool
    conflict_type: str | None
    semantic_note: str | None
    # Nhãn ẩn danh ("Người phỏng vấn 2") của những người CHƯA ghi note cho tiêu chí
    # này - đúng yêu cầu thiết kế "phải hiện rõ thiếu ai", không chỉ đếm số lượng.
    missing_interviewer_labels: list[str]


class RawNoteResponse(BaseModel):
    """Note gốc kèm nhãn ẩn danh (dùng chung interviewer_label với AggregationReport,
    xem app.services.aggregation.build_interviewer_labels) - HR/Council xem khi cần
    đối chiếu trực tiếp, đặc biệt khi semantic_note không tự tóm tắt được (LLM lỗi)."""

    criterion_id: uuid.UUID
    criterion_name: str
    interviewer_label: str
    score: int | None
    note_text: str | None


class AggregationReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    per_criterion_summary: list[CriterionSummary]
    overall_score: float | None
    overall_recommendation: str
    rationale_trace: str