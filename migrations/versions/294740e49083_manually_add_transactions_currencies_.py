"""Manually add transactions-currencies foreign key

Revision ID: 294740e49083
Revises: 545c9ac443b0
Create Date: 2024-12-11 00:47:04.044089

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '294740e49083'
down_revision: Union[str, None] = '545c9ac443b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Step 1: Add the currency_id column as nullable
    op.add_column('transactions', sa.Column(
        'currency_id', sa.Integer, nullable=True))

    # Step 2: Populate the currencies table with initial data
    op.execute("""
        INSERT INTO currencies (code, name, symbol, region)
        VALUES 
            ('USD', 'US Dollar', '$', 'United States'),
            ('CRC', 'Costa Rican Colón', '₡', 'Costa Rica')
    """)

    # Step 3: Populate the currency_id column based on the existing currency enum
    op.execute("""
        UPDATE transactions
        SET currency_id = (
            SELECT id
            FROM currencies
            WHERE currencies.code = transactions.currency::TEXT
        )
    """)

    # Step 4: Assign a default currency_id for rows where currency_id is still NULL
    op.execute("""
        UPDATE transactions
        SET currency_id = (
            SELECT id FROM currencies WHERE code = 'CRC'
        )
        WHERE currency_id IS NULL
    """)

    # Step 5: Make the currency_id column non-nullable
    op.alter_column('transactions', 'currency_id', nullable=False)

    # Step 6: Remove the old currency enum column
    op.drop_column('transactions', 'currency')

    # Step 7: Add the foreign key constraint
    op.create_foreign_key(
        'fk_transactions_currency_id',
        source_table='transactions',
        referent_table='currencies',
        local_cols=['currency_id'],
        remote_cols=['id']
    )


def downgrade():
    # Step 1: Drop the foreign key constraint
    op.drop_constraint('fk_transactions_currency_id',
                       'transactions', type_='foreignkey')

    # Step 2: Add back the old currency enum column
    op.add_column(
        'transactions',
        sa.Column('currency', sa.Enum(
            'USD', 'CRC', 'ARS', 'COL', 'MXN', name='currency'), nullable=False)
    )

    # Step 3: Populate the old currency column based on currency_id
    op.execute("""
        UPDATE transactions
        SET currency = (
            SELECT code
            FROM currencies
            WHERE currencies.id = transactions.currency_id
        )
    """)

    # Step 4: Drop the currency_id column
    op.drop_column('transactions', 'currency_id')

    # Step 5: Remove the inserted rows from the currencies table
    op.execute("""
        DELETE FROM currencies
        WHERE code IN ('USD', 'CRC', 'ARS', 'COL', 'MXN')
    """)
