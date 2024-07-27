from requests import Session

from ..models.transaction import TransactionTable
from ..repositories.generic_repository import GenericRepository
from ..schemas import DateRange


class TransactionRepository(GenericRepository[TransactionTable]):
    def __init__(self, db: Session):
        super().__init__(db, TransactionTable)
