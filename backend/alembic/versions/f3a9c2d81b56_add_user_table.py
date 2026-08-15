"""add user table

Revision ID: f3a9c2d81b56
Revises: b54bb688f164
Create Date: 2026-08-15

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "f3a9c2d81b56"
down_revision = "b54bb688f164"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.String(20),
            nullable=False,
            comment="hr_admin/interviewer/council",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_user_email", "user", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_user_email", table_name="user")
    op.drop_table("user")