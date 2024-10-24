from http import HTTPStatus
from typing import override

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (Bank, TransactionIDExistsError, TransactionTable,
                      generate_transaction_id)
from ..models.factories import BankServiceFactory, BankTransactionService
from ..repositories.transaction_repository import TransactionRepository
from ..schemas import (ApiResponse, CursorModel, DateRange,
                       Meta, SingleResponse,
                       Transaction, TransactionCreate, TransactionUpdate)
from .email_service import EmailReaderService
from .generic_service import GenericService


class TransactionService(
    GenericService[TransactionTable, TransactionCreate,
                   TransactionUpdate, Transaction]
):
    def __init__(self, db: Session, email_service: EmailReaderService):
        self.bac_service: BankTransactionService = BankServiceFactory.get_from_bank(
            Bank.BAC, db, email_service)
        self.repository: TransactionRepository = TransactionRepository(db)

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
        bac_transactions = self.bac_service.fetch_all_transactions_from_email(
            cursor=cursor, date_range=date_range)
        return bac_transactions
