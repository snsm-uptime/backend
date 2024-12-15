import hashlib
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Float, Integer, String, Text
from sqlalchemy.orm import relationship
from ._base import Base


def generate_transaction_id(bank: str, value: float, date: datetime) -> str:
    """
    Generate a unique transaction ID based on the bank, value, and date.
    """
    input_string = f"{bank}{value}{date.isoformat()}"
    return hashlib.sha256(input_string.encode()).hexdigest()


class TransactionTable(Base):
    __tablename__ = 'transactions'

    id = Column(String, primary_key=True, index=True)
    date = Column(DateTime, default=lambda: datetime.now(
        timezone.utc), nullable=False)
    value = Column(Float, nullable=False)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    # Establish relationship with the CurrencyTable
    currency = relationship('CurrencyTable', lazy='joined')
    business = Column(String, nullable=False)
    business_type = Column(String, nullable=True)
    bank_name = Column(String, nullable=False)
    bank_email = Column(String, nullable=False)
    # Replace Enum with ForeignKey or Integer if dynamic enums are needed
    expense_priority = Column(Integer, nullable=True)
    # Replace Enum with ForeignKey or Integer if dynamic enums are needed
    expense_type = Column(Integer, nullable=True)
    body = Column(Text, nullable=False)
