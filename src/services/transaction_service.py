from http import HTTPStatus
from typing import List, Optional, Tuple, override

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from email_transaction_extractor.email.client import EmailClient
from email_transaction_extractor.email.imap_search_criteria import \
    IMAPSearchCriteria
from email_transaction_extractor.exceptions import TransactionIDExistsError
from email_transaction_extractor.models.enums import Bank
from email_transaction_extractor.models.transaction import (
    TransactionTable, generate_transaction_id)
from email_transaction_extractor.repositories.transaction_repository import \
    TransactionRepository
from email_transaction_extractor.schemas.api_response import (
    ApiResponse, Meta, PaginatedResponse, SingleResponse)
from email_transaction_extractor.schemas.transaction import (Transaction,
                                                             TransactionCreate,
                                                             TransactionUpdate)
from email_transaction_extractor.services.email_service import EmailService
from email_transaction_extractor.services.generic_service import GenericService
from email_transaction_extractor.utils.dates import DateRange
from email_transaction_extractor.utils.decorators import timed_operation
from email_transaction_extractor.utils.parsers.bac_parser import \
    BacMessageParser
from email_transaction_extractor.utils.parsers.promerica_parser import \
    PromericaMessageParser


class TransactionService(GenericService[TransactionTable, TransactionCreate, TransactionUpdate, Transaction]):
    def __init__(self, db: Session):
        self.repository: TransactionRepository = TransactionRepository(db)
        super().__init__(TransactionTable,
                         TransactionCreate, TransactionUpdate, Transaction, self.repository)

    @override
    def create(self, obj_in: TransactionCreate) -> ApiResponse[SingleResponse[Transaction]]:
        transaction_id = generate_transaction_id(
            obj_in.bank_email, obj_in.value, obj_in.date)
        obj_in_data = obj_in.model_dump()
        obj_in_data['id'] = transaction_id
        db_obj = self.repository.model(**obj_in_data)
        try:
            db_obj, elapsed_time = self.repository.create(db_obj)
            # TODO: Add bank and bank_email to the transaction model to avoid type missmatch error
        except IntegrityError:
            raise TransactionIDExistsError(transaction_id)

        transaction = self.return_schema.model_validate(db_obj)

        return ApiResponse(
            meta=Meta(status=HTTPStatus.CREATED, request_time=elapsed_time,
                      message=f'Transaction created successfully'),
            data=SingleResponse(item=transaction)
        )

    def get_by_date(self, page_size: int, date_range: DateRange, cursor: Optional[str] = None) -> ApiResponse[PaginatedResponse[Transaction]]:

        filter = and_(TransactionTable.date >= date_range.start_date,
                      TransactionTable.date <= date_range.end_date)
        response = self.get_paginated(page_size, cursor, filter=filter)
        response.meta.message = \
            f'Transactions from {str(date_range)} retrieved successfuly'
        return response

    def fetch_emails_from_date(self, client: EmailClient, date_range: DateRange) -> ApiResponse[SingleResponse]:
        meta, time = self.refresh_database_with_emails_from_date(
            client, date_range)
        meta.request_time = time
        return ApiResponse(meta=meta)

    @timed_operation
    def refresh_database_with_emails_from_date(self, client: EmailClient, date_range: DateRange) -> Tuple[Meta, float]:
        transactions = self.__fetch_from_email_by_date(
            client, date_range)
        new_count = 0
        for obj in transactions:
            try:
                self.logger.info(
                    f'Processing transaction\tday={obj.date.isoformat()}\tbusiness={obj.business}')
                self.create(obj)
                new_count += 1
            except TransactionIDExistsError as e:
                self.logger.info(
                    f'Transaction ID {e.transaction_id} already exists for {obj.business}, skipping.')
                continue
            except IntegrityError as e:
                self.logger.error(
                    f'Integrity error while processing {obj.business}')
                continue
            except Exception as e:
                self.logger.error(
                    f'Unexpected error while processing {obj.business}')
                self.logger.exception(e)
                continue
        self.logger.info(
            f"{len(transactions)} Emails processed successfully. Created {new_count} new entries in the DB")

        meta = Meta(
            status=HTTPStatus.OK,
            message=f"{len(transactions)} Emails processed successfully. Created {new_count} new entries in the DB")
        return meta

    def __fetch_from_email_by_date(self, client: EmailClient, date_range: DateRange) -> List[TransactionCreate]:
        """
        Fetches transaction emails from specified banks within a given date range, parses the emails to extract transaction details,
        and returns a list of TransactionCreate objects.

        Args:
            client (EmailClient): An instance of EmailClient used to connect to the email server and fetch emails.
            date_range (DateRange): An instance of DateRange specifying the start and end dates for fetching emails.

        Returns:
            List[TransactionCreate]: A list of TransactionCreate objects containing the extracted transaction details from the emails.
        """
        service = EmailService(
            client,
            default_criteria=IMAPSearchCriteria().date_range(
                date_range.start_date, date_range.end_date)
        )
        bac_emails = service.get_mail_from_bank(Bank.BAC)
        self.logger.info('Fetched the BAC transaction emails')
        promerica_emails = service.get_mail_from_bank(
            Bank.PROMERICA, 'Comprobante de')
        self.logger.info('Fetched the PROMERICA transaction emails')
        transactions: list[TransactionCreate] = []

        for bank_emails, parser_class in [(bac_emails, BacMessageParser), (promerica_emails, PromericaMessageParser)]:
            for email in bank_emails:
                parser = parser_class(email)
                value, currency = parser.parse_value_and_currency()
                bank = Bank.BAC if parser_class == BacMessageParser else Bank.PROMERICA
                transaction = TransactionCreate(
                    date=parser.parse_date(),
                    value=value,
                    currency=currency,
                    business=parser.parse_business(),
                    business_type=parser.parse_business_type(),
                    bank_email=bank.email,
                    bank_name=bank.name,
                    body=parser.body,
                    expense_priority=None,
                    expense_type=None
                )
                transactions.append(transaction)

        self.logger.info('Extracted transaction details from emails')
        self.logger.info(f'Total transactions = {len(transactions)}')
        return transactions
