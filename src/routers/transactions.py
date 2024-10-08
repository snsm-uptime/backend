import logging
from http import HTTPStatus
from typing import Optional

from fastapi import APIRouter, Depends, Query
from requests import RequestException
from sqlalchemy import alias

from ..schemas import ApiResponse, CursorModel, DateRange
from ..services import TransactionService
from ..dependencies import get_transaction_service
from ..utils import create_json_response, create_exception_response

router = APIRouter(prefix="/transactions")

logger = logging.getLogger(__name__)


@router.post("/pull", response_model=ApiResponse)
def pull_transactions_from_email(
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
    result = transaction_service.pull_transactions_from_email(
        cursor, date_range)
    return create_json_response(result)


# @router.get("/", response_model=ApiResponse[PaginatedResponse[Transaction]])
# def get_all(cursor: Optional[str] = Query(None), page_size: int = Query(10), db: Session = Depends(get_db)):
#     service = TransactionService(db)
#     return service.get_paginated(cursor=cursor, page_size=page_size)


# @router.get("/by-date", response_model=ApiResponse[PaginatedResponse[Transaction]])
# def get_by_date(date_range: DateRange, cursor: Optional[str] = Query(None), page_size: int = Query(10), db: Session = Depends(get_db)):
#     service = TransactionService(db)
#     return service.get_by_date(cursor=cursor, page_size=page_size, date_range=DateRange(**date_range.model_dump()))


# @router.get("/{transaction_id}", response_model=ApiResponse[SingleResponse[Transaction]])
# def get_by_id(transaction_id: str, db: Session = Depends(get_db)):
#     service = TransactionService(db)
#     resp = service.get(transaction_id)
#     resp.meta.message = "Transaction retrieved successfully"
#     return resp


# @router.put("/{transaction_id}", response_model=Transaction)
# def update(transaction_id: int, transaction_data: TransactionCreate, db: Session = Depends(get_db)):
#     service = TransactionService(db)
#     return service.update_transaction(transaction_id, transaction_data.dict())


# @router.delete("/{transaction_id}", response_model=Transaction)
# def delete(transaction_id: int, db: Session = Depends(get_db)):
#     service = TransactionService(db)
#     return service.delete_transaction(transaction_id)


# @router.post("/", response_model=ApiResponse[SingleResponse[Transaction]])
# def create(transaction: TransactionCreate, db: Session = Depends(get_db)):
#     service = TransactionService(db)
#     return service.create(transaction)


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
