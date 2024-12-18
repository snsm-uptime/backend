from curses import meta
from functools import partial
from http import HTTPStatus
from logging import getLogger
from typing import List, Optional, Tuple, Union, override

from psycopg2.errors import DivisionByZero
from sqlalchemy import ColumnElement, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..services.currency_service import CurrencyService

from ..config import bank_config, config
from ..models import (Bank, TransactionIDExistsError, TransactionTable,
                      generate_transaction_id)
from ..models.enums import TimePeriod
from ..repositories.transaction_repository import TransactionRepository
from ..schemas import (ApiResponse, CursorModel, DateRange, EmailMessageModel,
                       Meta, PaginatedResponse, SingleResponse, Transaction,
                       TransactionCreate, TransactionUpdate)
from ..schemas.api_response import PaginationMeta
from ..schemas.currency import Currency
from ..schemas.transaction import TransactionMetricsByPeriodResult
from ..utils.pagination import PaginationDetails, ThreadedPaginator
from .email_service import EmailReaderService
from .generic_service import GenericService


def parse_email_to_transaction(m: EmailMessageModel, bank: Bank) -> TransactionCreate:
    parser = bank_config[bank].parser(m)
    value, currency = parser.parse_value_and_currency()
    business = parser.parse_business()
    transaction = TransactionCreate(
        bank_email=bank.email,
        bank_name=bank.name,
        business=business,
        business_type=parser.parse_business_type(),
        currency=currency,
        date=m.date,
        value=value,
        body=m.body.strip().replace('\n', ''),
        expense_priority=None,
        expense_type=None
    )
    return transaction


class TransactionService(
    GenericService[TransactionTable, TransactionCreate,
                   TransactionUpdate, Transaction]
):
    def __init__(self, db: Session, email_service: EmailReaderService, currency_service: CurrencyService):
        self.repository: TransactionRepository = TransactionRepository(db)
        self.email_service = email_service
        self.currency_service = currency_service

        super().__init__(
            TransactionTable,
            TransactionCreate,
            TransactionUpdate,
            Transaction,
            self.repository,
        )

    def get_expenses(self, date_range: DateRange) -> ApiResponse[SingleResponse[dict]]:
        data, exec_time = self.repository.get_expenses(date_range)
        return ApiResponse(
            meta=Meta(status=HTTPStatus.OK,
                      message=f"Got expenses from {date_range} in currency: USD, CRC", request_time=exec_time),
            data=SingleResponse(item=data)
        )

    @override
    def create(
        self, obj_in: TransactionCreate
    ) -> ApiResponse[SingleResponse[Transaction]]:
        transaction_id = generate_transaction_id(
            obj_in.bank_email, obj_in.value, obj_in.date
        )
        currency_response = self.currency_service.get_by_code(obj_in.currency)
        currency: Currency

        if currency_response.meta.status == HTTPStatus.OK:
            currency = currency_response.data.item
        else:
            new_currency_response = self.currency_service.create_from_code(
                obj_in.currency)
            currency = new_currency_response.data.item

        obj_in_data = obj_in.model_dump()
        obj_in_data["id"] = transaction_id
        obj_in_data['currency_id'] = currency.id
        del obj_in_data['currency']
        db_obj = self.repository.model(**obj_in_data)
        try:
            db_obj, elapsed_time = self.repository.create(db_obj)
        except IntegrityError:
            raise TransactionIDExistsError(transaction_id)

        # Map the currency relationship to the code
        transaction_data = self.return_schema.model_validate(
            {**db_obj.__dict__, "currency": db_obj.currency.code}
        )

        return ApiResponse(
            meta=Meta(
                status=HTTPStatus.CREATED,
                request_time=elapsed_time,
                message=f"Transaction created successfully {transaction_id}",
            ),
            data=SingleResponse(item=transaction_data),
        )

    def pull_transactions_from_email(
        self,
        cursor: CursorModel,
        date_range: DateRange,
    ) -> ApiResponse:
        existing_entries = []
        paginators: List[Tuple[ThreadedPaginator, Bank]] = []
        response_messages: List[str] = []
        empty_responses = 0
        new_entries = []
        for bank in bank_config.keys():
            def fetch_func(page=cursor.page): return self.email_service.fetch_emails_page_from_bank(
                bank=bank,
                mailbox=config.MAILBOX,
                date_range=date_range,
                page_size=cursor.page_size,
                page=page
            )
            emails: ApiResponse[PaginatedResponse[EmailMessageModel]] = fetch_func(
                page=cursor.page)
            response_messages.append(emails.meta.message)
            match emails.meta.status:
                case HTTPStatus.OK:
                    if emails.data:
                        pagination_metadata = emails.data.pagination
                        paginator = ThreadedPaginator[ApiResponse[PaginatedResponse[EmailMessageModel]]](
                            logger=getLogger(bank.name.upper()+'_ThreadPool'),
                            pagination_details=PaginationDetails(
                                page_size=pagination_metadata.page_size,
                                total_items=pagination_metadata.total_items
                            ),
                            process_function=fetch_func,
                            thread_count=config.EMAIL_PROCESSING_THREADS,
                            first_result=emails
                        )
                        paginators.append((paginator, bank))
                case HTTPStatus.PARTIAL_CONTENT:
                    self.logger.warning(emails.meta.message)
                    empty_responses += 1

        exec_time = 0.0
        for p, bank in paginators:
            pagination_result = p()
            bank_api_responses: List[ApiResponse[PaginatedResponse[EmailMessageModel]]
                                     ] = pagination_result[0]
            thread_pool_exec_time: float = pagination_result[1]
            exec_time += thread_pool_exec_time
            for api_response in bank_api_responses:
                if api_response:
                    for email in api_response.data.items:
                        transaction = parse_email_to_transaction(
                            email, bank)
                        try:
                            response = self.create(transaction)
                            if response.data:
                                new_entries.append(response.data.item.id)
                        except TransactionIDExistsError as e:
                            existing_entries.append(e.transaction_id)
                            response_messages.append(*e.args)
                        except Exception as e:
                            self.logger.exception(e)

        if empty_responses == len(bank_config.keys()):
            return ApiResponse(meta=Meta(
                status=HTTPStatus.PARTIAL_CONTENT,
                message=response_messages,
                request_time=0.0
            ))
        return ApiResponse(meta=Meta(
            status=HTTPStatus.OK,
            message=response_messages,
            request_time=exec_time
        ), data={
            'total_found': sum([p[0].total_items for p in paginators]),
            'new_entries': new_entries,
            'existing_entries': existing_entries
        })

    def get_paginated_from_bank(self, cursor: CursorModel, bank: Bank, date_range: Optional[DateRange] = None) -> ApiResponse[PaginatedResponse[Transaction]]:
        whereclause = TransactionTable.bank_name == bank.name
        if date_range:
            whereclause = and_(
                whereclause, date_range.contains(TransactionTable.date))
        return self.get_paginated(cursor, whereclause, order_by=TransactionTable.value)

    def get_metrics_by_period(self, date_range: DateRange, period: TimePeriod, currency: Currency) -> ApiResponse[SingleResponse[TransactionMetricsByPeriodResult]]:
        elapsed_time = 0
        data = None
        meta = None
        try:
            response, elapsed_time = self.repository.get_metrics_by_period(
                date_range, period, currency)
            meta = Meta(
                status=HTTPStatus.OK,
                message=f'Got metrics grouped by {
                    period.name} from {date_range}',
                request_time=elapsed_time
            )
            data = SingleResponse(item=response)
        except DivisionByZero:
            meta = Meta(
                status=HTTPStatus.NOT_ACCEPTABLE,
                message=f"Can't get metrics because there were no transactions in {
                    currency.name} from {date_range}",
                elapsed_time=0
            )

        return ApiResponse(meta=meta, data=data)

    def get_paginated(self, cursor: CursorModel, filter: Optional[ColumnElement] = None,
                      order_by: Optional[Union[ColumnElement,
                                               list[ColumnElement]]] = None
                      ) -> ApiResponse[PaginatedResponse[Transaction]]:
        current_page = cursor.page
        page_size = cursor.page_size

        total_items, count_elapsed_time = self.repository.count(filter)
        offset = (current_page - 1) * page_size
        db_objs, paginated_elapsed_time = self.repository.get_paginated(
            offset, page_size, filter, order_by)

        total_pages = (total_items + page_size - 1) // page_size
        request_time = count_elapsed_time + paginated_elapsed_time

        next_cursor = CursorModel(
            page=current_page + 1, page_size=page_size).encode() if current_page < total_pages else None
        prev_cursor = CursorModel(
            page=current_page - 1, page_size=page_size).encode() if current_page > 1 else None

        # Map the currency relationship to the code
        items = [self.return_schema.model_validate(
            {**obj.__dict__, "currency": obj.currency.code}) for obj in db_objs]

        meta = Meta(status=HTTPStatus.OK, request_time=request_time,
                    message="Transactions retrieved successfully")
        pagination = PaginationMeta(
            total_items=total_items,
            total_pages=total_pages,
            page_size=page_size,
            page=current_page,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor
        )

        response = ApiResponse(meta=meta, data=PaginatedResponse(
            pagination=pagination, items=items))
        return response
