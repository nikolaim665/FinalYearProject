"""add_alternative_answers_column

Revision ID: 35757c730081
Revises: ce8f50213406
Create Date: 2026-01-22 18:14:43.888702

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '35757c730081'
down_revision: Union[str, Sequence[str], None] = 'ce8f50213406'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('questions', sa.Column('alternative_answers', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('questions', 'alternative_answers')
