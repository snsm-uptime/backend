import hashlib
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Float, String, Text

from ..database import Base
from ..models.enums import ExpensePriority, ExpenseType


def generate_transaction_id(bank: str, value: float, date: datetime) -> str:
    # Create a string from the bank, value, and date
    input_string = f"{bank}{value}{date.isoformat()}"
    # Generate a SHA-256 hash of the input string
    transaction_id = hashlib.sha256(input_string.encode()).hexdigest()
    return transaction_id


class TransactionTable(Base):
    __tablename__ = 'transactions'

    id = Column(String, primary_key=True, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    value = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    business = Column(String, nullable=False)
    business_type = Column(String, nullable=True)
    bank_name = Column(String, nullable=False)
    bank_email = Column(String, nullable=False)
    expense_priority = Column(Enum(ExpensePriority), nullable=True)
    expense_type = Column(Enum(ExpenseType), nullable=True)
    body = Column(Text, nullable=False)
