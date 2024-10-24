from abc import abstractmethod
from functools import partial
from http import HTTPStatus
import json
from logging import getLogger
from typing import List, Optional

from pydantic import ValidationError
from requests import Session

from ..config import config
from ..models.enums import Bank
from ..parsers.bac_parser import BacMessageParser
from ..repositories.transaction_repository import TransactionRepository
from ..schemas.api_response import (ApiResponse, CursorModel, DateRange, Meta,
                                    PaginatedResponse, PaginationMeta,
                                    SingleResponse)
from ..schemas.email import EmailMessageModel
from ..schemas.transaction import TransactionCreate, TransactionsPageResponse
from ..services.email_service import EmailReaderService
from ..services.memcache_service import MemcacheService
from ..utils.pagination import PaginationDetails, ThreadedPaginator
from ..utils import hash_pagination_meta


class BankTransactionService:
    def __init__(self, db: Session, email_service: EmailReaderService):
        self.email_service = email_service
        self.repository: TransactionRepository = TransactionRepository(db)
        self.logger = getLogger(self.__class__.__name__)
        self.cache_service = MemcacheService('memcached')

    @abstractmethod
    def parse_email(self, email: EmailMessageModel) -> TransactionCreate:
        raise NotImplementedError

    @abstractmethod
    def _fetch_transactions_from_email(
            self,
            page: int,
            page_size: int,
            date_range: DateRange,
            total_items: Optional[int] = None,
    ) -> Optional[TransactionsPageResponse]:
        raise NotImplementedError

    @abstractmethod
    def pull_transactions_to_database(
        self,
        cursor: CursorModel,
        date_range: DateRange,
    ) -> ApiResponse[SingleResponse]:
        raise NotImplementedError

    def fetch_all_transactions_from_email(self, cursor: CursorModel, date_range: DateRange) -> ApiResponse[SingleResponse[List[TransactionsPageResponse]]]:
        transactions_response = self._fetch_transactions_from_email(
            page_size=cursor.page_size,
            page=1,
            date_range=date_range
        )

        fetch = partial(
            self._fetch_transactions_from_email,
            page_size=cursor.page_size,
            date_range=date_range,
            total_items=transactions_response.pagination_meta.total_items
        )

        bac_paginator = ThreadedPaginator[TransactionsPageResponse](
            self.logger,
            PaginationDetails(
                page_size=transactions_response.pagination_meta.page_size,
                total_items=transactions_response.pagination_meta.total_items
            ),
            config.EMAIL_PROCESSING_THREADS,
            fetch
        )
        transactions_response, exec_time = bac_paginator()
        self.logger.debug(
            f'Took {exec_time:.4f} seconds during threaded pagination')
        all_transactions = []
        for page_details in transactions_response:
            self.logger.debug(
                f'Added data from page {page_details.pagination_meta.current_page}/{page_details.pagination_meta.total_pages}')
            # move the set cache logic to the fetch function too.
            self.cache_service.set_transactions(page_details)
            all_transactions.extend(page_details.transactions)

        return ApiResponse(
            meta=Meta(
                status=HTTPStatus.OK,
                message=(f"Found {len(all_transactions)} in your Email's "
                         f"{config.MAILBOX} from {date_range}"),
                request_time=exec_time  # TODO: include time it took to save to cache
            ),
            data=SingleResponse(item=all_transactions)
        )


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

    def _fetch_transactions_from_email(
            self,
            page: int,
            page_size: int,
            date_range: DateRange,
            total_items: Optional[int] = None,
    ) -> Optional[TransactionsPageResponse]:
        # TODO: figure out why cache aint working
        if total_items:
            meta = PaginationMeta(
                total_items=total_items,
                page_size=page_size,
                current_page=page,
                total_pages=(total_items + page_size - 1) // page_size,
            )
            cached_values = self.cache_service.get_transactions(meta)
            if cached_values:
                obj = TransactionsPageResponse(
                    pagination_meta=meta, transactions=cached_values)
                return obj
        cursor = CursorModel(page=page, page_size=page_size)
        response: ApiResponse[PaginatedResponse[EmailMessageModel]] =\
            self.email_service.fetch_paginated_bac_email(
            config.MAILBOX,
            date_range.start_date,
            date_range.end_date,
            cursor=cursor)

        if response.data:
            return TransactionsPageResponse(pagination_meta=response.data.pagination, transactions=[self.parse_email(item) for item in response.data.items])


class BankServiceFactory:
    @ staticmethod
    def get_from_bank(bank: Bank, db: Session, email_service: EmailReaderService) -> BankTransactionService:
        services = {
            Bank.BAC: BacTransactionService,
            # TODO: Bank.PROMERICA:
        }
        return services[bank](db, email_service)
