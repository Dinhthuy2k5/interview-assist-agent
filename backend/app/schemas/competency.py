import uuid

from pydantic import BaseModel, ConfigDict, Field


class CriterionCreate(BaseModel):
    name: str
    weight: float = 1.0
    scoring_rubric: str


class CriterionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    weight: float
    scoring_rubric: str


class CompetencyFrameworkCreate(BaseModel):
    name: str
    description: str | None = None
    criteria: list[CriterionCreate] = Field(
        default_factory=list,
        description="Tạo framework kèm sẵn danh sách tiêu chí trong cùng 1 request",
    )


class CompetencyFrameworkUpdate(BaseModel):
    """Chỉ sửa name/description. Sửa criteria xử lý qua endpoint riêng ở sprint sau
    (cần cân nhắc: sửa/xoá criterion đang có Question tham chiếu sẽ ảnh hưởng dữ liệu cũ)."""

    name: str | None = None
    description: str | None = None


class CompetencyFrameworkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    criteria: list[CriterionResponse]