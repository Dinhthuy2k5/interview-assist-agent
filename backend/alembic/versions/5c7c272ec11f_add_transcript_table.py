"""add transcript table

Revision ID: 5c7c272ec11f
Revises: 96dbe49061f0
Create Date: 2026-08-17

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "5c7c272ec11f"
down_revision = "96dbe49061f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transcript",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interview_session.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "audio_file_path", sa.String(512), nullable=False, comment="Object key trong MinIO"
        ),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.String(20), server_default="pending", comment="pending/processing/completed/failed"
        ),
        sa.Column("retention_expiry", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("transcript")