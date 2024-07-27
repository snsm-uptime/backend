
from http import HTTPStatus
from logging import getLogger

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import requests
from sqlalchemy import Tuple

from ..utils.decorators import timed_operation

from ..schemas import EmailMessageModel, Meta, ApiResponse, CursorModel, PaginatedResponse


class EmailReaderService:
    def __init__(self):
        self.email_api_url = "http://email-reader:80"
        self.logger = getLogger(__class__.__name__)

    def fetch_paginated_bac_email(self, mailbox: str, start_date: str, end_date: str, cursor: CursorModel) -> ApiResponse[PaginatedResponse[EmailMessageModel]]:
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "senders": "notificacion@notificacionesbaccr.com",
            **cursor.model_dump()
        }
        response = requests.get(
            f"{self.email_api_url}/{mailbox}", params=params)
        response.raise_for_status()
        return ApiResponse(**response.json())

    def fetch_paginated_promerica_email(self, mailbox: str, start_date: str, end_date: str, cursor: CursorModel) -> ApiResponse[PaginatedResponse[EmailMessageModel]]:
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "senders": "info@promerica.fi.cr",
            "subject": "Comprobante",
            **cursor.model_dump()
        }
        response = requests.get(
            f"{self.email_api_url}/{mailbox}", params=params)
        response.raise_for_status()
        return ApiResponse[PaginatedResponse[EmailMessageModel]](**response.json())
