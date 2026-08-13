import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    level: str
    jd_file_path: str
    jd_text: str | None
    jd_parse_status: str
    framework_id: uuid.UUID
    created_by: str
    created_at: datetime
    updated_at: datetime


class JobUpdate(BaseModel):
    """HR sửa jd_text khi parse confidence thấp (needs_review)."""

    jd_text: str | None = None