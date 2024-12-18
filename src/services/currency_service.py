from http import HTTPStatus
from typing import Optional, Tuple, override

import requests
from sqlalchemy.orm import Session

from ..utils.dynamic_enum import remap_currency_codes

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
        code = remap_currency_codes(code)
        response = requests.get(
            f'https://restcountries.com/v3.1/currency/{code}')
        response.raise_for_status()
        data = response.json()[0]
        return CurrencyCreate(
            code=code,
            name=data['currencies'][code]['name'],
            symbol=data['currencies'][code]['symbol'],
            region=data['name']['common']
        )

    def create_from_code(self, code: str) -> ApiResponse[SingleResponse[Currency]]:
        code = remap_currency_codes(code)
        new_entry, time_get_meta = self.get_currency_metadata(code)
        response = self.create(new_entry)
        response.meta.request_time += time_get_meta
        response.meta.message = f"Created a new currency {
            response.data.item.name}"
        return response

    def get_by_code(self, code: str) -> ApiResponse[SingleResponse[Currency]]:
        code = remap_currency_codes(code)
        result, elapsed_time = self.repository.filter_by_code(code)
        if result:
            return ApiResponse(
                meta=Meta(
                    message=f'Found data from {result.name}',
                    request_time=elapsed_time, status=HTTPStatus.OK),
                data=SingleResponse(item=result)
            )
        else:
            return ApiResponse(
                meta=Meta(
                    message=f'That currency isn\'t registered',
                    request_time=elapsed_time, status=HTTPStatus.NOT_FOUND),
            )
