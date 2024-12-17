from http import HTTPStatus
from typing import Optional, Tuple, override

import requests
from sqlalchemy.orm import Session

from ..models.currency import CurrencyTable
from ..repositories.currency_repository import CurrencyRepository
from ..repositories.generic_repository import GenericRepository
from ..schemas.api_response import ApiResponse, Meta, SingleResponse
from ..schemas.currency import Currency, CurrencyCreate, CurrencyUpdate
from ..services.generic_service import GenericService
from ..utils.decorators import timed_operation


class CurrencyService(GenericService[CurrencyTable, CurrencyCreate, CurrencyUpdate, Currency]):
    def __init__(self, db: Session):
        self.repository: CurrencyRepository = CurrencyRepository(db)

        super().__init__(
            CurrencyTable,
            CurrencyCreate,
            CurrencyUpdate,
            Currency,
            self.repository
        )

    @timed_operation
    def get_currency_metadata(self, code: str) -> Tuple[CurrencyCreate, float]:
        response = requests.get(
            f'https://restcountries.com/v3.1/currency/{code}')
        response.raise_for_status()
        data = response.json()
        return CurrencyCreate(
            code,
            name=data['currencies'][code]['name'],
            symbol=data['currencies'][code]['symbol'],
            region=data['region']
        )

    def create_from_code(self, code: str) -> ApiResponse[SingleResponse[Currency]]:
        db_currencies, time_get_all = self.repository.get_all()
        existing_currency: Optional[Currency] = None
        for i in db_currencies:
            if i.code == code:
                existing_currency = i

        if not existing_currency:
            new_entry, time_get_meta = self.get_currency_metadata(code)
            response = self.create(new_entry)
            response.meta.request_time += time_get_meta + time_get_all
            response.meta.message = f"Created a new currency {
                response.data.item.name}"
            return response
        else:
            return ApiResponse(meta=Meta(message="That code is already assigned to a currency in the database", request_time=time_get_all, status=HTTPStatus.FOUND),
                               data=SingleResponse(item=existing_currency))
