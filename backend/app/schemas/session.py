import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SessionStatus = Literal["scheduled", "in_progress", "completed"]


class SessionCreate(BaseModel):
    job_id: uuid.UUID
    candidate_name: str
    candidate_info: str | None = None
    scheduled_at: datetime
    interviewer_ids: list[uuid.UUID] = Field(min_length=1)


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    candidate_name: str
    candidate_info: str | None
    scheduled_at: datetime
    status: str


class SessionStatusUpdate(BaseModel):
    status: SessionStatus


class QuestionForSession(BaseModel):
    """Câu hỏi + rubric hiện cho interviewer trong lúc phỏng vấn - không lộ rationale
    (nội bộ, không cần thiết cho người hỏi) hay is_approved (đã lọc sẵn chỉ câu đã
    duyệt mới tới được đây). criterion_name/scoring_rubric lấy kèm từ Criterion -
    thiếu 2 field này thì interviewer không biết chấm điểm 1-5 dựa trên tiêu chuẩn
    nào, mất hết ý nghĩa của việc "dùng chung rubric cho mọi interviewer"."""

    id: uuid.UUID
    criterion_id: uuid.UUID
    criterion_name: str
    scoring_rubric: str
    content: str


class NoteUpsert(BaseModel):
    score: int | None = Field(default=None, ge=1, le=5)
    note_text: str | None = None


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    criterion_id: uuid.UUID
    score: int | None
    note_text: str | None


class SessionDetailResponse(BaseModel):
    """Trả về cho interviewer khi vào 1 session: thông tin session, câu hỏi đã
    duyệt kèm rubric, và CHỈ note của chính người gọi API - không lộ note người khác."""

    session: SessionResponse
    questions: list[QuestionForSession]
    my_notes: list[NoteResponse]