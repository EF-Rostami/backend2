"""appointment

Revision ID: bc3623212a04
Revises: ac84df018dd7
Create Date: 2025-10-20 18:00:22.981577

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc3623212a04'
down_revision: Union[str, Sequence[str], None] = 'ac84df018dd7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
