"""merge events and appointment branches

Revision ID: 80271c32de7b
Revises: bc3623212a04, add_events
Create Date: 2025-10-21 09:47:48.178927

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '80271c32de7b'
down_revision: Union[str, Sequence[str], None] = ('bc3623212a04', 'add_events')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
