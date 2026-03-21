"""add_unique_partial_index_active_timer

Revision ID: 9f656725dd5e
Revises: 789469fc36c6
Create Date: 2026-03-20 18:36:53.947443

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f656725dd5e'
down_revision: Union[str, Sequence[str], None] = '789469fc36c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_time_entries_one_active_per_user",
        "time_entries",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("ended_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_time_entries_one_active_per_user", table_name="time_entries")
