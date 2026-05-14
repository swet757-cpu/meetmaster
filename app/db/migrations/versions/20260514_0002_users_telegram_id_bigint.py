"""use bigint for Telegram user IDs

Revision ID: 20260514_0002
Revises: 20260511_0001
Create Date: 2026-05-14

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260514_0002"
down_revision: str | None = "20260511_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "telegram_id",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "telegram_id",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=False,
    )
