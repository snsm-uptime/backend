from abc import abstractmethod
from functools import partial
from http import HTTPStatus
from logging import getLogger
from typing import List, Optional, Tuple
from pydantic import ValidationError
from requests import Session

from backend.src.utils.pagination import PaginationDetails, ThreadedPaginator

from ..parsers.bac_parser import BacMessageParser
from ..schemas.api_response import ApiResponse, CursorModel, DateRange, Meta, PaginatedResponse, PaginationMeta, SingleResponse
from ..config import config

from ..schemas.transaction import TransactionCreate

from ..repositories.transaction_repository import TransactionRepository
from ..schemas.email import EmailMessageModel
from ..services.email_service import EmailReaderService
from ..models.enums import Bank


class BankTransactionService:
    def __init__(self, db: Session, email_service: EmailReaderService):
        self.email_service = email_service
        self.repository: TransactionRepository = TransactionRepository(db)
        self.logger = getLogger(self.__class__.__name__)

    @abstractmethod
    def parse_email(self, email: EmailMessageModel) -> TransactionCreate:
        raise NotImplementedError

    @abstractmethod
    def fetch_transactions_from_email(
            self,
            page: int,
            page_size: int,
            date_range: DateRange,
    ) -> Optional[Tuple[PaginationMeta, List[TransactionCreate]]]:
        raise NotImplementedError

    @abstractmethod
    def pull_transactions_to_database(
        self,
        cursor: CursorModel,
        date_range: DateRange,
    ) -> ApiResponse[SingleResponse]:
        raise NotImplementedError


class BacTransactionService(BankTransactionService):
    def __init__(self, db: Session, email_service: EmailReaderService):
        super().__init__(db, email_service)

    def parse_email(self, email: EmailMessageModel) -> TransactionCreate:
        parser = BacMessageParser(email)
        value, currency = parser.parse_value_and_currency()
        try:
            transaction = TransactionCreate(
                bank_email=Bank.BAC.email,
                bank_name=Bank.BAC.name,
                business=parser.parse_business(),
                business_type=parser.parse_business_type(),
                currency=currency,
                date=email.date,
                value=value,
                body=email.body,
                expense_priority=None,
                expense_type=None
            )
            return transaction
        except ValidationError as ve:
            self.logger.exception(ve)

    def fetch_transactions_from_email(
            self,
            page: int,
            page_size: int,
            date_range: DateRange,
    ) -> Optional[Tuple[PaginationMeta, List[TransactionCreate]]]:
        cursor = CursorModel(page=page, page_size=page_size)
        response: ApiResponse[PaginatedResponse[EmailMessageModel]] =\
            self.email_service.fetch_paginated_bac_email(
            config.MAILBOX,
            date_range.start_date,
            date_range.end_date,
            cursor=cursor)

        if response.data:
            return response.data.pagination, self._transform_paginated_api_response(response)

    def fetch_all_transactions_from_email(self, cursor: CursorModel, date_range: DateRange) -> ApiResponse[SingleResponse]:
        fetch = partial(self.fetch_transactions_from_email,
                        page_size=cursor.page_size, date_range=date_range)
        bac_transactions = fetch(page=1)
        bac_paginator = ThreadedPaginator[Tuple[PaginationMeta, List[TransactionCreate]]](
            self.logger,
            PaginationDetails(
                page_size=bac_transactions[0].page_size,
                total_items=bac_transactions[0].total_items
            ),
            config.EMAIL_PROCESSING_THREADS,
            fetch
        )
        bac_transactions, exec_time = bac_paginator()

        return ApiResponse(
            meta=Meta(
                status=HTTPStatus.OK,
                message=(f"Found {len(bac_transactions)} in your Email's"
                         f"{config.MAILBOX} from {date_range}"),
                request_time=exec_time
            ),
            data=SingleResponse(bac_transactions)
        )


class BankServiceFactory:
    def get_from_bank(bank: Bank) -> BankTransactionService:
        pass
