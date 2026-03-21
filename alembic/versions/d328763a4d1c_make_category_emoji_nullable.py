"""make_category_emoji_nullable

Revision ID: d328763a4d1c
Revises: 9f656725dd5e
Create Date: 2026-03-20 18:44:49.777615

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd328763a4d1c'
down_revision: Union[str, Sequence[str], None] = '9f656725dd5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("categories", "emoji",
                    existing_type=sa.String(10),
                    nullable=True)


def downgrade() -> None:
    op.execute("UPDATE categories SET emoji = '❓' WHERE emoji IS NULL")
    op.alter_column("categories", "emoji",
                    existing_type=sa.String(10),
                    nullable=False)
