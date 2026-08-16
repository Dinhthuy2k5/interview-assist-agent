import uuid
from datetime import UTC, date, datetime

from pydantic import BaseModel, ConfigDict, computed_field


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
    application_deadline: date | None
    is_closed: bool
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def status(self) -> str:
        """Tính động từ application_deadline/is_closed, không lưu DB - "closed" nếu
        HR đóng tay HOẶC đã quá hạn nộp hồ sơ."""
        if self.is_closed:
            return "closed"
        if self.application_deadline is not None and self.application_deadline < datetime.now(UTC).date():
            return "closed"
        return "open"


class JobUpdate(BaseModel):
    """HR sửa jd_text khi parse confidence thấp (needs_review). Cũng dùng để set/sửa
    hạn nộp hồ sơ hoặc đóng tuyển tay (is_closed)."""

    jd_text: str | None = None
    application_deadline: date | None = None
    is_closed: bool | None = None