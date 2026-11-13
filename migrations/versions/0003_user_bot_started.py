"""Факт первого /start в боте: users.bot_started_at.

ВНИМАНИЕ: миграция создана, но НЕ применена. Применять вручную после проверки.
Существующие пользователи получают NULL (backfill не делается).
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("bot_started_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "bot_started_at")
