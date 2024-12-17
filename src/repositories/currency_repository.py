from sqlalchemy.orm import Session
from ..models.currency import CurrencyTable
from ..repositories.generic_repository import GenericRepository


class CurrencyRepository(GenericRepository[CurrencyTable]):
    def __init__(self, db: Session):
        super().__init__(db, CurrencyTable)
