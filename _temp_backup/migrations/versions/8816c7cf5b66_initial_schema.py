"""Initial schema

Revision ID: 8816c7cf5b66
Revises: None
Create Date: 2026-05-19 21:09:04.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8816c7cf5b66'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'occupation_visas',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('occupation', sa.String(), nullable=False),
        sa.Column('visa_subclass', sa.String(), nullable=False),
        sa.Column('stream', sa.String(), nullable=False),
        sa.Column('scraped_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_occupation_visas_occupation'), 'occupation_visas', ['occupation'], unique=False)
    op.create_index(op.f('ix_occupation_visas_visa_subclass'), 'occupation_visas', ['visa_subclass'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_occupation_visas_visa_subclass'), table_name='occupation_visas')
    op.drop_index(op.f('ix_occupation_visas_occupation'), table_name='occupation_visas')
    op.drop_table('occupation_visas')
