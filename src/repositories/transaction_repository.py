import os
from typing import Tuple

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import text
from sqlalchemy.orm import Session


from ..models import TimePeriod, TransactionTable, Currency
from ..repositories.generic_repository import GenericRepository
from ..schemas.api_response import DateRange
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
            date_range.model_dump(), currencies=Currency))
        self.logger.debug(query.text)
        result = self.db.execute(query).fetchone()
        expenses = {currency.name: getattr(
            result, currency.name.lower()) for currency in Currency}
        return expenses

    @timed_operation
    def get_expenses_by_period(self, date_range: DateRange, period: TimePeriod) -> Tuple[dict[str, float], float]:
        template = self._db_env.get_template('period_expense_metrics.pgsql')
        query = text(template.render(date_range.model_dump()))
        response = self.db.execute(query)
        dollars, colones = response.fetchone()
        return {
            'USD': dollars,
            'CRC': colones
        }
