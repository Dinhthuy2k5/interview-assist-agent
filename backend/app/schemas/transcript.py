import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TranscriptResponse(BaseModel):
    """Không có audio_file_path - đó là object key nội bộ trong MinIO, không có lý
    do gì để lộ ra client, giống việc UserResponse không bao giờ trả password_hash."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    text: str | None
    status: str
    retention_expiry: datetime