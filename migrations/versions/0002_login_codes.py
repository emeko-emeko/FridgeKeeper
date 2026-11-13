"""Коды входа через бота: таблица login_codes.

ВНИМАНИЕ: миграция создана, но НЕ применена. Применять вручную после проверки.
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"


def upgrade() -> None:
    op.create_table(
        "login_codes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("confirmed_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("used_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_login_codes_code_hash", "login_codes", ["code_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_login_codes_code_hash", table_name="login_codes")
    op.drop_table("login_codes")
