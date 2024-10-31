from curses import meta
from functools import partial
from http import HTTPStatus
from logging import getLogger
from typing import List, Tuple, override

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..utils.pagination import PaginationDetails, ThreadedPaginator

from ..config import bank_config, config
from ..models import (Bank, TransactionIDExistsError, TransactionTable,
                      generate_transaction_id)
from ..repositories.transaction_repository import TransactionRepository
from ..schemas import (ApiResponse, CursorModel, DateRange, Meta,
                       SingleResponse, Transaction, TransactionCreate,
                       TransactionUpdate, EmailMessageModel,  PaginatedResponse)
from .email_service import EmailReaderService
from .generic_service import GenericService


def parse_email_to_transaction(m: EmailMessageModel, bank: Bank) -> TransactionCreate:
    parser = bank_config[bank].parser(m)
    value, currency = parser.parse_value_and_currency()
    transaction = TransactionCreate(
        bank_email=bank.email,
        bank_name=bank.name,
        business=parser.parse_business(),
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
    def __init__(self, db: Session, email_service: EmailReaderService):
        # self.bac_service: BankTransactionService = BankServiceFactory.get_from_bank(Bank.BAC, db, email_service) # This was DEPRECATED
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
                            response_messages.append(response.meta.message)
                            if response.data:
                                new_entries.append(response.data.item.id)
                        except TransactionIDExistsError as e:
                            existing_entries.append(e.transaction_id)
                            response_messages.append(*e.args)

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
