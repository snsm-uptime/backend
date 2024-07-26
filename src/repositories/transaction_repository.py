from typing import List, Tuple
from requests import Session
from email_transaction_extractor.repositories.generic_repository import GenericRepository
from email_transaction_extractor.models.transaction import TransactionTable
from email_transaction_extractor.utils.dates import DateRange
from email_transaction_extractor.utils.decorators import timed_operation


class TransactionRepository(GenericRepository[TransactionTable]):
    def __init__(self, db: Session):
        super().__init__(db, TransactionTable)
