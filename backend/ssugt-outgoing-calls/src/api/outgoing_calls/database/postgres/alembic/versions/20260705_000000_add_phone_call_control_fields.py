"""add_phone_call_control_fields

Revision ID: 20260705_000000
Revises: 20260620_102256_4fb3d988cbbc
Create Date: 2026-07-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260705_000000"
down_revision: Union[str, Sequence[str], None] = "4fb3d988cbbc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "phone_calls",
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.add_column(
        "phone_calls",
        sa.Column("is_control", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("phone_calls", "is_control")
    op.drop_column("phone_calls", "created_at")

