from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from ..models.enums import ExpensePriority, ExpenseType


class TransactionBase(BaseModel):
    bank_name: str
    bank_email: str
    business: str
    currency: str
    date: datetime
    value: float

    body: Optional[str] = None
    business_type: Optional[str] = None
    expense_priority: Optional[ExpensePriority] = None
    expense_type: Optional[ExpenseType] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(TransactionBase):
    pass


class Transaction(TransactionBase):
    id: str

    model_config = ConfigDict(
        from_attributes=True
    )
