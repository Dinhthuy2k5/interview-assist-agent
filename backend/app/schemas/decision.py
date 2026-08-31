import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

DecisionValue = Literal["hired", "rejected", "on_hold"]


class DecisionCreate(BaseModel):
    decision: DecisionValue
    rationale: str = Field(min_length=1)


class DecisionResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    decided_by: uuid.UUID
    # Hiện tên thật (không ẩn danh) - khác InterviewerNote, xem docstring model.
    decided_by_name: str
    decision: str
    rationale: str
    created_at: datetime