import logging
from datetime import datetime
from http import HTTPStatus
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..config import config
from ..database import get_db
from ..schemas.api_response import (ApiResponse, DateRange, Meta,
                                    PaginatedResponse, SingleResponse)
from ..schemas.transaction import Transaction, TransactionCreate
from ..services.transaction_service import TransactionService

router = APIRouter(prefix='/transactions')

logger = logging.getLogger(__name__)


@router.get("/", response_model=ApiResponse[PaginatedResponse[Transaction]])
def get_all(cursor: Optional[str] = Query(None), page_size: int = Query(10), db: Session = Depends(get_db)):
    service = TransactionService(db)
    return service.get_paginated(cursor=cursor, page_size=page_size)


@router.get("/by-date", response_model=ApiResponse[PaginatedResponse[Transaction]])
def get_by_date(date_range: DateRange, cursor: Optional[str] = Query(None), page_size: int = Query(10), db: Session = Depends(get_db)):
    service = TransactionService(db)
    return service.get_by_date(cursor=cursor, page_size=page_size, date_range=DateRange(**date_range.model_dump()))


@router.get("/{transaction_id}", response_model=ApiResponse[SingleResponse[Transaction]])
def get_by_id(transaction_id: str, db: Session = Depends(get_db)):
    service = TransactionService(db)
    resp = service.get(transaction_id)
    resp.meta.message = "Transaction retrieved successfully"
    return resp


@router.put("/{transaction_id}", response_model=Transaction)
def update(transaction_id: int, transaction_data: TransactionCreate, db: Session = Depends(get_db)):
    service = TransactionService(db)
    return service.update_transaction(transaction_id, transaction_data.dict())


@router.delete("/{transaction_id}", response_model=Transaction)
def delete(transaction_id: int, db: Session = Depends(get_db)):
    service = TransactionService(db)
    return service.delete_transaction(transaction_id)


@router.post("/", response_model=ApiResponse[SingleResponse[Transaction]])
def create(transaction: TransactionCreate, db: Session = Depends(get_db)):
    service = TransactionService(db)
    return service.create(transaction)


@router.post("/refresh", response_model=ApiResponse)
def refresh_transactions_by_date(range: DateRange, db: Session = Depends(get_db)):
    """
    Create transactions based on the start date provided in the request.

    Args:
        request: RefreshTransactionsRequest object containing the start date.
        db: Database session.

    Raises:
        HTTPException: If the start date is in the future.

    Returns:
        None
    """
    service = TransactionService(db)
    today = datetime.now()

    if range.start_date > today:
        return ApiResponse(meta=Meta(
            status=HTTPStatus.BAD_REQUEST,
            message="Start date cannot be in the future",
        ))

    if range.end_date > today:
        range.end_date = today

    date_range = DateRange(start_date=range.start_date,
                           end_date=range.end_date, days_ago=range.days_ago)

    with EmailClient(
        email_user=config.EMAIL_USER,
        email_pass=config.EMAIL_PASSWORD,
        server=ImapServer.GOOGLE.value,
        mailbox=config.EMAIL_MAILBOX
    ) as email_client:
        logger.info(
            f"Starting transaction creation process for date range: {date_range}")
        response = service.fetch_emails_from_date(
            email_client,
            date_range
        )
        return response
