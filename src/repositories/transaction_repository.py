from typing import List, Optional, Tuple
from sqlalchemy import ColumnElement, and_, select
from sqlalchemy.orm import Session
from ..models.transaction import TransactionTable
from ..repositories.generic_repository import GenericRepository


class TransactionRepository(GenericRepository[TransactionTable]):
    def __init__(self, db: Session):
        super().__init__(db, TransactionTable)
