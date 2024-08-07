from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from .database import get_db
from .services import TransactionService, EmailReaderService

transaction_service_instance: Optional[TransactionService] = None
email_reader_service_instance: Optional[EmailReaderService] = None


def get_email_reader_service() -> EmailReaderService:
    global email_reader_service_instance
    if not email_reader_service_instance:
        return EmailReaderService()
    return email_reader_service_instance


def get_transaction_service(
        db: Session = Depends(get_db),
        email_service: EmailReaderService = Depends(get_email_reader_service)
) -> TransactionService:
    global transaction_service_instance
    if not transaction_service_instance:
        return TransactionService(db, email_service)
    return transaction_service_instance
