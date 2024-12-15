from functools import lru_cache
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.models.currency import CurrencyTable
from src.database import get_db
from src.utils.dynamic_enum import generate_dynamic_enum
from enum import Enum
import logging

logger = logging.getLogger(__name__)


@lru_cache
def cached_currency_enum():
    logger.info("Generating cached currency enum...")
    session = get_db()  # Explicit session management for caching
    try:
        return generate_dynamic_enum(session, CurrencyTable, "code")
    finally:
        session.close()
