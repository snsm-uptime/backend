from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from ..services.currency_service import CurrencyService

from ..database import get_db
from ..services import EmailReaderService, TransactionService

currency_service_instance: Optional[CurrencyService] = None
email_reader_service_instance: Optional[EmailReaderService] = None
transaction_service_instance: Optional[TransactionService] = None


def get_currency_service(
        db: Session = Depends(get_db)
) -> CurrencyService:
    global currency_service_instance
    if not currency_service_instance:
        return CurrencyService(db)
    return currency_service_instance


def get_email_reader_service() -> EmailReaderService:
    global email_reader_service_instance
    if not email_reader_service_instance:
        return EmailReaderService()
    return email_reader_service_instance


def get_transaction_service(
        db: Session = Depends(get_db),
        email_service: EmailReaderService = Depends(get_email_reader_service),
        currency_service: CurrencyService = Depends(get_currency_service)
) -> TransactionService:
    global transaction_service_instance
    if not transaction_service_instance:
        return TransactionService(db, email_service, currency_service)
    return transaction_service_instance
