"""add interview session, session interviewer, interviewer note tables

Revision ID: 96dbe49061f0
Revises: a7c41f9d2e83
Create Date: 2026-08-16

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "96dbe49061f0"
down_revision = "a7c41f9d2e83"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "interview_session",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job.id"), nullable=False),
        sa.Column("candidate_name", sa.String(255), nullable=False),
        sa.Column("candidate_info", sa.Text(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status", sa.String(20), server_default="scheduled", comment="scheduled/in_progress/completed"
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "session_interviewer",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interview_session.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "interviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("session_id", "interviewer_id", name="uq_session_interviewer"),
    )

    op.create_table(
        "interviewer_note",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interview_session.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "interviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id"), nullable=False
        ),
        sa.Column(
            "criterion_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("criterion.id"), nullable=False
        ),
        sa.Column("score", sa.Integer(), nullable=True, comment="1-5, null nếu chưa chấm"),
        sa.Column("note_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "session_id", "interviewer_id", "criterion_id", name="uq_note_session_interviewer_criterion"
        ),
    )


def downgrade() -> None:
    op.drop_table("interviewer_note")
    op.drop_table("session_interviewer")
    op.drop_table("interview_session")