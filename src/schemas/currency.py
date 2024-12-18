from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CurrencyBase(BaseModel):
    code: str
    name: Optional[str]
    symbol: Optional[str]
    region: Optional[str]
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class CurrencyCreate(CurrencyBase):
    pass


class CurrencyUpdate(CurrencyBase):
    pass


class Currency(CurrencyBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True
    )
