from datetime import datetime
from email.utils import parseaddr
from functools import partial
from http import HTTPStatus
from logging import getLogger
from typing import Callable, List, Optional, Tuple, override

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..types import EmailFetcher

from ..config import config
from ..models import (TransactionIDExistsError, TransactionTable,
                      generate_transaction_id, Bank)
from ..parsers import BacMessageParser, BaseMessageParser, PromericaMessageParser
from ..repositories.transaction_repository import TransactionRepository
from ..schemas import (ApiResponse, CursorModel, PaginationMeta, DateRange, EmailMessageModel,
                       Meta, PaginatedResponse, SingleResponse, Transaction,
                       TransactionCreate, TransactionUpdate)
from ..utils.pagination import PaginationDetails, ThreadedPaginator
from .email_service import EmailReaderService
from .generic_service import GenericService


class TransactionService(
    GenericService[TransactionTable, TransactionCreate,
                   TransactionUpdate, Transaction]
):
    def __init__(self, db: Session, email_service: EmailReaderService):
        self.repository: TransactionRepository = TransactionRepository(db)
        self.email_service = email_service
        super().__init__(
            TransactionTable,
            TransactionCreate,
            TransactionUpdate,
            Transaction,
            self.repository,
        )

    @override
    def create(
        self, obj_in: TransactionCreate
    ) -> ApiResponse[SingleResponse[Transaction]]:
        transaction_id = generate_transaction_id(
            obj_in.bank_email, obj_in.value, obj_in.date
        )
        obj_in_data = obj_in.model_dump()
        obj_in_data["id"] = transaction_id
        db_obj = self.repository.model(**obj_in_data)
        try:
            db_obj, elapsed_time = self.repository.create(db_obj)
            # TODO: Add bank and bank_email to the transaction model to avoid type missmatch error
        except IntegrityError:
            raise TransactionIDExistsError(transaction_id)

        transaction = self.return_schema.model_validate(db_obj)

        return ApiResponse(
            meta=Meta(
                status=HTTPStatus.CREATED,
                request_time=elapsed_time,
                message=f"Transaction created successfully {transaction.id}",
            ),
            data=SingleResponse(item=transaction),
        )

    def _transform_paginated_api_response(self, response: ApiResponse[PaginatedResponse[EmailMessageModel]]) -> List[TransactionCreate]:
        transactions: List[TransactionCreate] = []
        for m in response.data.items:
            parser: BaseMessageParser
            bank_name: str = ''
            bank_email = parseaddr(m.from_email)[1]
            match bank_email:
                case Bank.BAC.email:
                    parser = BacMessageParser(m)
                    bank_name = Bank.BAC.name
                case Bank.PROMERICA.email:
                    parser = PromericaMessageParser(m)
                    bank_name = Bank.PROMERICA.name
                    # ignore these types of emails
                    # TODO: implement pago de tarjeta de credito parser
                    if 'Pago de Tarjeta de Credito' in m.subject:
                        self.logger.warning(
                            f'Ignored email because it was a card payment')
                        continue
                case _:
                    raise ValueError(f'Parser not found for {m.from_email}')

            value, currency = parser.parse_value_and_currency()
            try:
                transaction = TransactionCreate(
                    bank_email=bank_email,
                    bank_name=bank_name,
                    business=parser.parse_business(),
                    business_type=parser.parse_business_type(),
                    currency=currency,
                    date=m.date,
                    value=value,
                    body=m.body,
                    expense_priority=None,
                    expense_type=None
                )
                transactions.append(transaction)
            except ValidationError as ve:
                self.logger.exception(ve)
        return transactions

    def pull_transactions_from_email(
        self,
        cursor: CursorModel,
        date_range: DateRange,
    ) -> ApiResponse:

        fetch_promerica = partial(
            self.fetch_transactions_from_email, page_size=cursor.page_size,
            fetch_function=self.email_service.fetch_paginated_promerica_email,
            date_range=date_range)
        fetch_bac = partial(
            self.fetch_transactions_from_email, page_size=cursor.page_size,
            fetch_function=self.email_service.fetch_paginated_bac_email,
            date_range=date_range)

        all_transactions: List[Tuple[PaginationMeta,
                                     List[TransactionCreate]]] = []
        total_time: float = 0.0

        if bac_transactions := fetch_bac(page=cursor.page):
            bac_paginator = ThreadedPaginator[Tuple[PaginationMeta, List[TransactionCreate]]](
                getLogger('BacThreadPool'),
                PaginationDetails(
                    page_size=bac_transactions[0].page_size,
                    total_items=bac_transactions[0].total_items
                ),
                config.EMAIL_PROCESSING_THREADS,
                fetch_bac
            )
            bac_transactions, bac_execution_time = bac_paginator()
            total_time += bac_execution_time
            all_transactions.append(bac_transactions)

        if promerica_transactions := fetch_promerica(page=cursor.page):
            promerica_paginator = ThreadedPaginator[Tuple[PaginationMeta, List[TransactionCreate]]](
                getLogger('PromericaThreadPool'),
                PaginationDetails(
                    page_size=promerica_transactions[0].page_size,
                    total_items=promerica_transactions[0].total_items
                ),
                config.EMAIL_PROCESSING_THREADS,
                fetch_promerica
            )

            promerica_transactions, promerica_execution_time = promerica_paginator()
            total_time += promerica_execution_time
            all_transactions.append(promerica_transactions)

        # Craft response based on process
        return ApiResponse(meta=Meta(
            status=HTTPStatus.OK,
            message=(f"Found {len(all_transactions)} in your Email's"
                     f"{config.MAILBOX} from {date_range}"),
            request_time=total_time
        ))

    # def __fetch_from_email_by_date(self, client: EmailClient, date_range: DateRange) -> List[TransactionCreate]:
    #     """
    #     Fetches transaction emails from specified banks within a given date range, parses the emails to extract transaction details,
    #     and returns a list of TransactionCreate objects.

    #     Args:
    #         client (EmailClient): An instance of EmailClient used to connect to the email server and fetch emails.
    #         date_range (DateRange): An instance of DateRange specifying the start and end dates for fetching emails.

    #     Returns:
    #         List[TransactionCreate]: A list of TransactionCreate objects containing the extracted transaction details from the emails.
    #     """
    #     service = EmailService(
    #         client,
    #         default_criteria=IMAPSearchCriteria().date_range(
    #             date_range.start_date, date_range.end_date)
    #     )
    #     bac_emails = service.get_mail_from_bank(Bank.BAC)
    #     self.logger.info('Fetched the BAC transaction emails')
    #     promerica_emails = service.get_mail_from_bank(
    #         Bank.PROMERICA, 'Comprobante de')
    #     self.logger.info('Fetched the PROMERICA transaction emails')
    #     transactions: list[TransactionCreate] = []

    #     for bank_emails, parser_class in [(bac_emails, BacMessageParser), (promerica_emails, PromericaMessageParser)]:
    #         for email in bank_emails:
    #             parser = parser_class(email)
    #             value, currency = parser.parse_value_and_currency()
    #             bank = Bank.BAC if parser_class == BacMessageParser else Bank.PROMERICA
    #             transaction = TransactionCreate(
    #                 date=parser.parse_date(),
    #                 value=value,
    #                 currency=currency,
    #                 business=parser.parse_business(),
    #                 business_type=parser.parse_business_type(),
    #                 bank_email=bank.email,
    #                 bank_name=bank.name,
    #                 body=parser.body,
    #                 expense_priority=None,
    #                 expense_type=None
    #             )
    #             transactions.append(transaction)

    #     self.logger.info('Extracted transaction details from emails')
    #     self.logger.info(f'Total transactions = {len(transactions)}')
    #     return transactions
