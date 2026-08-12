"""add llm_usage_log table

Revision ID: b54bb688f164
Revises: e2614e6b7131
Create Date: 2026-08-12

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "b54bb688f164"
down_revision = "e2614e6b7131"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "llm_usage_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "service",
            sa.String(50),
            nullable=False,
            comment="question_gen / aggregation_semantic_check / ...",
        ),
        sa.Column("tokens_in", sa.Integer(), nullable=False),
        sa.Column("tokens_out", sa.Integer(), nullable=False),
        sa.Column(
            "cost_estimate",
            sa.Numeric(10, 6),
            nullable=False,
            comment="USD, tính theo đơn giá model tại thời điểm gọi",
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("llm_usage_log")