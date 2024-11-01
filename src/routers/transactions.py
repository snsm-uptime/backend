import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import alias

from ..dependencies import get_transaction_service
from ..models.enums import Bank
from ..schemas import ApiResponse, CursorModel, DateRange
from ..schemas.api_response import PaginatedResponse, SingleResponse
from ..schemas.transaction import Transaction
from ..services import TransactionService
from ..utils import create_json_response

router = APIRouter(prefix="/transactions")

logger = logging.getLogger(__name__)


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
    cursor = CursorModel(page=page, page_size=page_size, cursor=cursor_str)
    return transaction_service.get_paginated(cursor=cursor)


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


# @router.post("/refresh", response_model=ApiResponse)
# def refresh_transactions_by_date(range: DateRange, db: Session = Depends(get_db)):
#     """
#     Create transactions based on the start date provided in the request.

#     Args:
#         request: RefreshTransactionsRequest object containing the start date.
#         db: Database session.

#     Raises:
#         HTTPException: If the start date is in the future.

#     Returns:
#         None
#     """
#     service = TransactionService(db)
#     today = datetime.now()

#     if range.start_date > today:
#         return ApiResponse(meta=Meta(
#             status=HTTPStatus.BAD_REQUEST,
#             message="Start date cannot be in the future",
#         ))

#     if range.end_date > today:
#         range.end_date = today

#     date_range = DateRange(start_date=range.start_date,
#                            end_date=range.end_date, days_ago=range.days_ago)

#     # fetch and create the transactions based on emails from that date
#     pass
