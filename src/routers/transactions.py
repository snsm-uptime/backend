import logging
from http import HTTPStatus
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func

from ..dependencies import get_transaction_service
from ..dependencies.currency_enum import cached_currency_enum
from ..models.enums import Bank, TimePeriod
from ..models.transaction import TransactionTable
from ..schemas import ApiResponse, CursorModel, DateRange
from ..schemas.api_response import Meta, PaginatedResponse, SingleResponse
from ..schemas.currency import Currency
from ..schemas.transaction import Transaction, TransactionMetricsByPeriodResult
from ..services import TransactionService
from ..utils import create_json_response

router = APIRouter(prefix="/transactions")

logger = logging.getLogger(__name__)


@router.get("/metrics", response_model=ApiResponse[SingleResponse[List[TransactionMetricsByPeriodResult]]])
def get_expenses(
    date_range: DateRange = Depends(),
    period: TimePeriod = Query(TimePeriod.MONTHLY),
    currency: str = Query('CRC'),
    transaction_service: TransactionService = Depends(get_transaction_service),
):
    enm = cached_currency_enum()
    try:
        return transaction_service.get_metrics_by_period(date_range, period, enm[currency])
    except KeyError:
        return ApiResponse(meta=Meta(status=HTTPStatus.NOT_FOUND, message=f'{currency.upper()} has no records in the system', request_time=0.0))


@router.get("/expenses", response_model=ApiResponse[SingleResponse[dict]])
def get_expenses(
    date_range: DateRange = Depends(),
    transaction_service: TransactionService = Depends(get_transaction_service),
):
    return transaction_service.get_expenses(date_range)


@router.post("/pull", response_model=ApiResponse)
def pull_transactions_from_email(
    date_range: DateRange = Depends(),
    cursor_str: Optional[str] = Query(
        None, description="Cursor for pagination", alias="cursor"
    ),
    page_size: Optional[int] = Query(
        None, description="Number of items per page"),
    transaction_service: TransactionService = Depends(get_transaction_service),
):
    cursor = CursorModel(page_size=page_size, cursor=cursor_str)
    result = transaction_service.pull_transactions_from_email(
        cursor, date_range)
    return create_json_response(result)


@router.get("/promerica", response_model=ApiResponse[PaginatedResponse[Transaction]])
def get_all_promerica(
    date_range: DateRange = Depends(),
    cursor_str: Optional[str] = Query(
        None, description="Cursor for pagination", alias="cursor"
    ),
    page: Optional[int] = Query(None, description="Current page"),
    page_size: Optional[int] = Query(
        None, description="Number of items per page"),
    transaction_service: TransactionService = Depends(get_transaction_service),

):
    if (date_range.end_date is None) and (date_range.start_date is None):
        date_range = None
    cursor = CursorModel(page=page, page_size=page_size, cursor=cursor_str)
    return transaction_service.get_paginated_from_bank(cursor=cursor, bank=Bank.PROMERICA, date_range=date_range)


@router.get("/bac", response_model=ApiResponse[PaginatedResponse[Transaction]])
def get_all_bac(
    date_range: DateRange = Depends(),
    cursor_str: Optional[str] = Query(
        None, description="Cursor for pagination", alias="cursor"
    ),
    page: Optional[int] = Query(None, description="Current page"),
    page_size: Optional[int] = Query(
        None, description="Number of items per page"),
    transaction_service: TransactionService = Depends(get_transaction_service),

):
    if (date_range.end_date is None) and (date_range.start_date is None):
        date_range = None
    cursor = CursorModel(page=page, page_size=page_size, cursor=cursor_str)
    return transaction_service.get_paginated_from_bank(cursor=cursor, bank=Bank.BAC, date_range=date_range)

# @router.get("/by-date", response_model=ApiResponse[PaginatedResponse[Transaction]])
# def get_by_date(date_range: DateRange, cursor: Optional[str] = Query(None), page_size: int = Query(10), db: Session = Depends(get_db)):
#     service = TransactionService(db)
#     return service.get_by_date(cursor=cursor, page_size=page_size, date_range=DateRange(**date_range.model_dump()))


@router.get("/{transaction_id}", response_model=ApiResponse[SingleResponse[Transaction]])
def get_by_id(transaction_id: str, transaction_service: TransactionService = Depends(get_transaction_service)):
    resp = transaction_service.get(transaction_id)
    resp.meta.message = "Transaction retrieved successfully"
    return resp


@router.get("/", response_model=ApiResponse[PaginatedResponse[Transaction]])
def get_all(
    date_range: DateRange = Depends(),
    cursor_str: Optional[str] = Query(
        None, description="Cursor for pagination", alias="cursor"
    ),
    page: Optional[int] = Query(None, description="Current page"),
    page_size: Optional[int] = Query(
        None, description="Number of items per page"),
    transaction_service: TransactionService = Depends(get_transaction_service),

):
    whereclause = date_range.contains(TransactionTable.date)
    cursor = CursorModel(page=page, page_size=page_size, cursor=cursor_str)
    return transaction_service.get_paginated(cursor=cursor, filter=whereclause, order_by=[func.date(TransactionTable.date).desc(), TransactionTable.business, TransactionTable.value.desc()])
