"""Change currency column to Enum(Currency)

Revision ID: 3ef7301bab9d
Revises: 94dd7f108c4e
Create Date: 2024-11-25 06:40:15.103015

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ef7301bab9d'
down_revision: Union[str, None] = '94dd7f108c4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    currency_enum = sa.Enum('CRC', 'USD', 'MXP',
                            name='currency', create_type=True)
    time_period_enum = sa.Enum(
        'daily', 'weekly', 'monthly', 'yearly', name='time_period', create_type=True)

    # Create the enum types in the database
    currency_enum.create(op.get_bind(), checkfirst=True)
    time_period_enum.create(op.get_bind(), checkfirst=True)
    op.execute(
        """
        ALTER TABLE transactions
        ALTER COLUMN currency TYPE currency
        USING currency::text::currency
        """
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # Revert the 'currency' column back to String
    op.execute(
        """
        ALTER TABLE transactions
        ALTER COLUMN currency TYPE text
        USING currency::text
        """
    )

    # Drop the enum types
    time_period_enum = sa.Enum(
        'daily', 'weekly', 'monthly', 'yearly', name='time_period')
    time_period_enum.drop(op.get_bind(), checkfirst=True)

    currency_enum = sa.Enum('CRC', 'USD', name='currency')
    currency_enum.drop(op.get_bind(), checkfirst=True)
