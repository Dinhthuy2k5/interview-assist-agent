import uuid

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPk, gen_uuid


class CompetencyFramework(Base, TimestampMixin):
    """Khung năng lực dùng làm nguồn sự thật duy nhất cho việc sinh câu hỏi
    và chấm điểm — Question Gen Agent KHÔNG được tự bịa tiêu chí ngoài framework này."""

    __tablename__ = "competency_framework"

    id: Mapped[uuid.UUID] = mapped_column(UUIDPk, primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    criteria: Mapped[list["Criterion"]] = relationship(
        back_populates="framework", cascade="all, delete-orphan"
    )


class Criterion(Base, TimestampMixin):
    """Một tiêu chí cụ thể trong khung năng lực, VD 'Problem solving', kèm
    trọng số và rubric chấm điểm (mô tả từng mức 1-5) để đảm bảo minh bạch."""

    __tablename__ = "criterion"

    id: Mapped[uuid.UUID] = mapped_column(UUIDPk, primary_key=True, default=gen_uuid)
    framework_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("competency_framework.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    weight: Mapped[float] = mapped_column(Numeric(3, 2), default=1.0)
    scoring_rubric: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Mô tả từng mức điểm 1-5, dùng chung cho mọi interviewer"
    )

    framework: Mapped["CompetencyFramework"] = relationship(back_populates="criteria")