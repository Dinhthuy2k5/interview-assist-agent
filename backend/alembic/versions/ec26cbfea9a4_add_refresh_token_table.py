"""add refresh_token table

Revision ID: ec26cbfea9a4
Revises: 8f1a3c6e9b02
Create Date: 2026-08-23

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "ec26cbfea9a4"
down_revision = "8f1a3c6e9b02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "refresh_token",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_refresh_token_token_hash", "refresh_token", ["token_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_refresh_token_token_hash", table_name="refresh_token")
    op.drop_table("refresh_token")