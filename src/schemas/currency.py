from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from ..models.enums import ExpensePriority, ExpenseType
from .api_response import PaginationMeta


class CurrencyBase(BaseModel):
    code: str
    name: Optional[str]
    symbol: Optional[str]
    region: Optional[str]
    created_at: datetime


class CurrencyCreate(CurrencyBase):
    pass


class CurrencyUpdate(CurrencyBase):
    pass


class Currency(CurrencyBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True
    )
