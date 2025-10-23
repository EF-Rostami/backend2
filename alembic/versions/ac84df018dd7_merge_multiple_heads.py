"""merge multiple heads

Revision ID: ac84df018dd7
Revises: e78657cd3535, add_absence_excuses
Create Date: 2025-10-20 14:33:17.273837

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac84df018dd7'
down_revision: Union[str, Sequence[str], None] = ('e78657cd3535', 'add_absence_excuses')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
