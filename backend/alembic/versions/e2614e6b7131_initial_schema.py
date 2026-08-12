"""initial schema: competency_framework, criterion, job, question

Revision ID: e2614e6b7131
Revises:
Create Date: 2026-08-12

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e2614e6b7131"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "competency_framework",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "criterion",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "framework_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("competency_framework.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("weight", sa.Numeric(3, 2), server_default="1.0"),
        sa.Column(
            "scoring_rubric",
            sa.Text(),
            nullable=False,
            comment="Mô tả từng mức điểm 1-5, dùng chung cho mọi interviewer",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "job",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("level", sa.String(50), nullable=False, comment="fresher/junior/senior"),
        sa.Column(
            "jd_file_path", sa.String(512), nullable=False, comment="Object key trong MinIO"
        ),
        sa.Column("jd_text", sa.Text(), nullable=True),
        sa.Column(
            "jd_parse_status",
            sa.String(20),
            server_default="pending",
            comment="pending/parsed/needs_review",
        ),
        sa.Column(
            "framework_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("competency_framework.id"),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "question",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "criterion_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("criterion.id"), nullable=False
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "rationale",
            sa.Text(),
            nullable=False,
            comment="Giải thích vì sao câu hỏi này đo được tiêu chí đó",
        ),
        sa.Column("generated_by", sa.String(20), server_default="agent", comment="agent/human_edited"),
        sa.Column("is_sensitive_flagged", sa.Boolean(), server_default=sa.false()),
        sa.Column("sensitive_flag_reason", sa.Text(), nullable=True),
        sa.Column(
            "is_approved",
            sa.Boolean(),
            server_default=sa.false(),
            comment="HR phải duyệt trước khi câu hỏi dùng được trong session",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("question")
    op.drop_table("job")
    op.drop_table("criterion")
    op.drop_table("competency_framework")