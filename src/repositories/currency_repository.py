from typing import Optional, Tuple

from sqlalchemy.orm import Session

from ..models.currency import CurrencyTable
from ..repositories.generic_repository import GenericRepository
from ..schemas.currency import Currency
from ..utils.decorators import timed_operation


class CurrencyRepository(GenericRepository[CurrencyTable]):
    def __init__(self, db: Session):
        super().__init__(db, CurrencyTable)

    @timed_operation
    def filter_by_code(self, code: str) -> Tuple[Optional[Currency], float]:
        result = self.db.query(
            CurrencyTable).filter_by(code=code).first()
        return result if not result else Currency.model_validate(result)
