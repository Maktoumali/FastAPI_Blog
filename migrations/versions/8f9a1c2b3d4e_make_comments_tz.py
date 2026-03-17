"""make comments timezone-aware

Revision ID: 8f9a1c2b3d4e
Revises: 7373cb154983
Create Date: 2026-03-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f9a1c2b3d4e'
down_revision: Union[str, Sequence[str], None] = '7373cb154983'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: make comment timestamps timezone-aware.

    Note: depending on your database backend (SQLite vs Postgres), the
    column-alter operation may be limited. If you use SQLite, consider
    recreating the table or using a manual migration strategy.
    """
    op.alter_column(
        'comments',
        'created_at',
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
    )

    op.alter_column(
        'comments',
        'updated_at',
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema: revert comment timestamps to naive DateTime."""
    op.alter_column(
        'comments',
        'created_at',
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=False,
    )

    op.alter_column(
        'comments',
        'updated_at',
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=True,
    )
