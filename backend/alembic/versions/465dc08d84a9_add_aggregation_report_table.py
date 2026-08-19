"""add aggregation_report table

Revision ID: 465dc08d84a9
Revises: 5c7c272ec11f
Create Date: 2026-08-18

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "465dc08d84a9"
down_revision = "5c7c272ec11f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "aggregation_report",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interview_session.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "per_criterion_summary",
            postgresql.JSON(),
            nullable=False,
            comment="List[{criterion_id, criterion_name, scores, average, has_conflict, "
            "conflict_type, semantic_note, missing_interviewer_count}]",
        ),
        sa.Column(
            "overall_score",
            sa.Numeric(3, 2),
            nullable=True,
            comment="Điểm trung bình có trọng số, null nếu chưa có note nào",
        ),
        sa.Column(
            "overall_recommendation",
            sa.String(50),
            nullable=False,
            comment="Đề xuất tuyển / Cần thảo luận thêm / Không đề xuất - Chỉ tư vấn",
        ),
        sa.Column(
            "rationale_trace",
            sa.Text(),
            nullable=False,
            comment="Narrative giải thích - bắt buộc, không được chỉ trả số trần trụi",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("aggregation_report")