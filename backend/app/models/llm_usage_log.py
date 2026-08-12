import uuid
from datetime import datetime

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPk, gen_uuid


class LlmUsageLog(Base):
    """Log mỗi lần gọi LLM (Question Gen Agent, Aggregation semantic check...).
    Log riêng bảng này (không dùng TimestampMixin) vì đây là bản ghi bất biến —
    không có khái niệm 'updated_at', chỉ có 1 mốc thời gian duy nhất khi request xảy ra.

    Dùng để: (1) giám sát chi phí thực tế so với ước tính ở bước Phân tích,
    (2) cảnh báo sớm nếu 1 service nào đó gọi LLM bất thường nhiều."""

    __tablename__ = "llm_usage_log"

    id: Mapped[uuid.UUID] = mapped_column(UUIDPk, primary_key=True, default=gen_uuid)
    service: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="question_gen / aggregation_semantic_check / ..."
    )
    tokens_in: Mapped[int] = mapped_column(nullable=False)
    tokens_out: Mapped[int] = mapped_column(nullable=False)
    cost_estimate: Mapped[float] = mapped_column(
        Numeric(10, 6), nullable=False, comment="USD, tính theo đơn giá model tại thời điểm gọi"
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())