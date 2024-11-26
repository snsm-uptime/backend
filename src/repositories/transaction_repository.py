import os
from typing import List, Optional, Tuple

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..models import Currency, TimePeriod, TransactionTable
from ..repositories.generic_repository import GenericRepository
from ..schemas.api_response import DateRange
from ..schemas.transaction import TransactionMetricsByPeriodResult
from ..utils.decorators import timed_operation


class TransactionRepository(GenericRepository[TransactionTable]):
    def __init__(self, db: Session):
        super().__init__(db, TransactionTable)
        template_dir = os.path.join(os.path.dirname(__file__), 'db')
        self._db_env = Environment(loader=FileSystemLoader(template_dir))

    @timed_operation
    def get_expenses(self, date_range: DateRange) -> Tuple[dict[str, float], float]:
        template = self._db_env.get_template('expenses.pgsql')
        query = text(template.render(
            date_range.model_dump(), currencies=Currency, decimals=5))
        self.logger.debug(query.text)
        result = self.db.execute(query).fetchone()
        expenses = {currency.name: round(float(getattr(
            result, currency.name.lower())), 2) for currency in Currency}
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
