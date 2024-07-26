from typing import Optional
from pydantic import BaseModel


class PydanticValidationError(BaseModel):
    field: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    input: Optional[str] = None

    def __str__(self):
        return f"[{self.field}={self.input}] {self.message}"


class TransactionIDExistsError(Exception):
    def __init__(self, transaction_id: str):
        self.transaction_id = transaction_id
        super().__init__(
            f"Transaction with ID {transaction_id} already exists.")
