from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from logging import getLogger
from typing import List, Optional, override

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..utils.pagination import PaginationDetails, ThreadedPaginator

from ..config import config
from ..models import TransactionIDExistsError, TransactionTable, generate_transaction_id
from ..repositories.transaction_repository import TransactionRepository
from ..schemas import (
    ApiResponse,
    CursorModel,
    DateRange,
    Meta,
    SingleResponse,
    Transaction,
    TransactionCreate,
    TransactionUpdate,
)
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

    def pull_transactions_from_email(
        self,
        cursor: CursorModel,
        date_range: DateRange,
    ) -> ApiResponse:
        # TODO: paginate through all pages in order to create the transactions
        promerica_response = self.email_service.fetch_paginated_promerica_email(
            config.MAILBOX, date_range.start_date, date_range.end_date, cursor
        )
        # TODO: paginate through all pages in order to create the transactions
        bac_response = self.email_service.fetch_paginated_bac_email(
            config.MAILBOX, date_range.start_date, date_range.end_date, cursor
        )
        # TODO: Implement threading to paginate everything
        request_time = (
            promerica_response.meta.request_time + bac_response.meta.request_time
        )
        transactions: List[Transaction] = []

        def iterate_promerica(cursor: Optional[str]) -> ApiResponse:
            pass

        paginator = ThreadedPaginator(
            getLogger('PromericaThreadPool'), pagination_details=PaginationDetails())

        # Craft response based on process
        return ApiResponse(
            meta=Meta(
                status=HTTPStatus.CREATED,
                message=f"Found {len(transactions)} in your Email's {
                    config.MAILBOX} from {date_range}",
                request_time=request_time,
            ),
        )

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
