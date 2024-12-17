import logging
from functools import lru_cache

from src.database import get_db
from src.models.currency import CurrencyTable
from src.utils.dynamic_enum import generate_dynamic_enum

logger = logging.getLogger(__name__)


@lru_cache
def cached_currency_enum():
    logger.info("Generating cached currency enum...")
    session = next(get_db())  # Explicit session management for caching
    try:
        return generate_dynamic_enum(session, CurrencyTable, "code")
    finally:
        session.close()
