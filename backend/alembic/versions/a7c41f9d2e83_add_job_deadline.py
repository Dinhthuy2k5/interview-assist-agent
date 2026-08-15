"""add job application_deadline and is_closed

Revision ID: a7c41f9d2e83
Revises: f3a9c2d81b56
Create Date: 2026-08-15

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a7c41f9d2e83"
down_revision = "f3a9c2d81b56"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job", sa.Column("application_deadline", sa.Date(), nullable=True))
    op.add_column(
        "job",
        sa.Column("is_closed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("job", "is_closed")
    op.drop_column("job", "application_deadline")