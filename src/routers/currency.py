import logging
from typing import List

from fastapi import APIRouter, Depends

from ..dependencies.service_getters import get_currency_service
from ..schemas.api_response import ApiResponse, SingleResponse
from ..schemas.currency import Currency
from ..services.currency_service import CurrencyService

router = APIRouter(prefix="/currency")

logger = logging.getLogger(__name__)


@router.get("/", response_model=ApiResponse[SingleResponse[List[Currency]]])
def get_all(currency_service: CurrencyService = Depends(get_currency_service)):
    data = currency_service.get_all()
    return data
