import os
from collections import defaultdict
from typing import List, Optional, Tuple

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..dependencies.currency_enum import cached_currency_enum
from ..models import TimePeriod, TransactionTable
from ..repositories.generic_repository import GenericRepository
from ..schemas.api_response import DateRange
from ..schemas.currency import Currency
from ..schemas.transaction import TransactionMetricsByPeriodResult
from ..utils.decorators import timed_operation


class TransactionRepository(GenericRepository[TransactionTable]):
    def __init__(self, db: Session):
        super().__init__(db, TransactionTable)
        template_dir = os.path.join(os.path.dirname(__file__), 'db')
        self._db_env = Environment(loader=FileSystemLoader(template_dir))

    @timed_operation
    def get_expenses(self, date_range: DateRange) -> Tuple[Optional[dict[str, Optional[float]]], float]:
        template = self._db_env.get_template('expenses.pgsql')
        currency_enum = cached_currency_enum()
        query = text(template.render(
            date_range.model_dump(), currencies=currency_enum, decimals=5))
        self.logger.debug(query.text)
        result = self.db.execute(query).fetchall()
        expenses = {
            currency[1]: currency[0] for currency in self.db.execute(query).fetchall()
        }
        return expenses

    @timed_operation
    def get_metrics_by_period(
        self, date_range: DateRange, period: TimePeriod, currency: Currency
    ) -> Tuple[List[TransactionMetricsByPeriodResult], float]:
        query = text(self._db_env.get_template('period_expense_metrics.pgsql').render(
            date_range.model_dump(), period=period.value, currency=currency.value
        ))
        row = self.db.execute(query).fetchall()
        metrics: List[TransactionMetricsByPeriodResult] = []
        if row:
            for i in row:
                metrics.append(
                    TransactionMetricsByPeriodResult(**i._mapping))
        return metrics
