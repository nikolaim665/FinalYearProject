"""add_answer_explanation_column

Revision ID: a1b2c3d4e5f6
Revises: 35757c730081
Create Date: 2026-02-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '35757c730081'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add answer_explanation column to questions table."""
    op.add_column('questions', sa.Column('answer_explanation', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove answer_explanation column from questions table."""
    op.drop_column('questions', 'answer_explanation')
