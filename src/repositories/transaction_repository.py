import os
from typing import Tuple

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..models.transaction import TransactionTable
from ..repositories.generic_repository import GenericRepository
from ..schemas.api_response import DateRange
from ..utils.decorators import timed_operation


class TransactionRepository(GenericRepository[TransactionTable]):
    def __init__(self, db: Session):
        super().__init__(db, TransactionTable)
        template_dir = os.path.join(os.path.dirname(__file__), 'db')
        self._db_env = Environment(loader=FileSystemLoader(template_dir))

    @timed_operation
    def get_expenses(self, date_range: DateRange) -> Tuple[dict, float]:
        template = self._db_env.get_template('expenses.pgsql')
        query = text(template.render(date_range.model_dump()))
        response = self.db.execute(query)
        dollars, colones = response.fetchone()
        return {
            'dollars': dollars,
            'colones': colones
        }
