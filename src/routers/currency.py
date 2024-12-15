from enum import Enum
import logging

from fastapi import APIRouter, Query

from ..schemas.api_response import SingleResponse, ApiResponse

from ..dependencies.currency_enum import cached_currency_enum


router = APIRouter(prefix="/currency")

logger = logging.getLogger(__name__)


@router.get("/", response_model=ApiResponse[SingleResponse[dict]])
def list_currencies(currency: Enum = Query(None, enum=cached_currency_enum())):
    return {"message": f"Selected currency: {currency}"}
