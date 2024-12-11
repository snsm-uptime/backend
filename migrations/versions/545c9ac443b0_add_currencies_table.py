"""Add currencies table

Revision ID: 545c9ac443b0
Revises: 3ef7301bab9d
Create Date: 2024-12-11 00:04:07.379117

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '545c9ac443b0'
down_revision: Union[str, None] = '3ef7301bab9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create the currencies table
    op.create_table(
        'currencies',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('code', sa.String(3), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('symbol', sa.String(5), nullable=True),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text(
            'CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('idx_currency_code', 'currencies', ['code'])


def downgrade():
    # Drop the currencies table
    op.drop_index('idx_currency_code', table_name='currencies')
    op.drop_table('currencies')
