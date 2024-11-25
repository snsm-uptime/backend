from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from ..models.enums import Currency, ExpensePriority, ExpenseType
from .api_response import PaginationMeta


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


class TransactionsPageResponse(BaseModel):
    pagination_meta: PaginationMeta
    transactions: List[TransactionCreate]


class TransactionMetricsByPeriodResult(BaseModel):
    period_start: datetime
    currency: Currency
    total: float
    transaction_count: int
    avg_transaction: float
    min_value: float
    max_value: float
    period_currency_pct: float
