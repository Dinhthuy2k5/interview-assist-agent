"""add session_decision and audit_log tables

Revision ID: 8f1a3c6e9b02
Revises: 465dc08d84a9
Create Date: 2026-08-21

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "8f1a3c6e9b02"
down_revision = "465dc08d84a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "session_decision",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interview_session.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "decided_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id"), nullable=False
        ),
        sa.Column("decision", sa.String(20), nullable=False, comment="hired/rejected/on_hold"),
        sa.Column(
            "rationale",
            sa.Text(),
            nullable=False,
            comment="Lý do quyết định - bắt buộc, không được để trống",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_session_decision_session_id", "session_decision", ["session_id"], unique=False
    )

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id"), nullable=True
        ),
        sa.Column(
            "action",
            sa.String(50),
            nullable=False,
            comment="login_success/login_failed/user_created/user_updated/decision_created",
        ),
        sa.Column("target_type", sa.String(50), nullable=True),
        sa.Column("target_id", sa.String(255), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_log_created_at", table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_index("ix_session_decision_session_id", table_name="session_decision")
    op.drop_table("session_decision")