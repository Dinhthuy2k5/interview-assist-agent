import uuid

from pydantic import BaseModel, ConfigDict


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    criterion_id: uuid.UUID
    content: str
    rationale: str
    generated_by: str
    is_sensitive_flagged: bool
    sensitive_flag_reason: str | None
    is_approved: bool


class QuestionUpdate(BaseModel):
    """HR sửa nội dung câu hỏi và/hoặc duyệt. Sửa content -> tự set generated_by=human_edited."""

    content: str | None = None
    is_approved: bool | None = None