"""Отметка «Использовано» у продукта и имя пользователя: products.used_at, users.first_name.

ВНИМАНИЕ: миграция создана, но НЕ применена. Применять вручную после проверки.
Существующие строки получают NULL (backfill не делается).
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("first_name", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "first_name")
    op.drop_column("products", "used_at")
