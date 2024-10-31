"""Initial migration

Revision ID: 94dd7f108c4e
Revises: 
Create Date: 2024-10-31 19:06:53.777913

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94dd7f108c4e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('transactions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=True),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('currency', sa.String(), nullable=False),
    sa.Column('business', sa.String(), nullable=False),
    sa.Column('business_type', sa.String(), nullable=True),
    sa.Column('bank_name', sa.String(), nullable=False),
    sa.Column('bank_email', sa.String(), nullable=False),
    sa.Column('expense_priority', sa.Enum('MUST', 'WANT', 'NEED', name='expensepriority'), nullable=True),
    sa.Column('expense_type', sa.Enum('TAXES', 'GROCERIES', 'EATING_OUT', 'ENTERTAINMENT', 'TRANSPORT', 'SELF_CARE', 'PET', 'GIFT', name='expensetype'), nullable=True),
    sa.Column('body', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_transactions_id'), table_name='transactions')
    op.drop_table('transactions')
    # ### end Alembic commands ###
