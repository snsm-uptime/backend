from datetime import datetime
from logging import getLogger

import requests

from ..schemas import (
    EmailMessageModel,
    ApiResponse,
    CursorModel,
    PaginatedResponse,
)


class EmailReaderService:
    def __init__(self):
        self.email_api_url = "http://email-reader:80"
        self.logger = getLogger(__class__.__name__)

    def fetch_paginated_bac_email(
        self,
        mailbox: str,
        start_date: datetime,
        end_date: datetime,
        cursor: CursorModel,
    ) -> ApiResponse[PaginatedResponse[EmailMessageModel]]:
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "senders": "notificacion@notificacionesbaccr.com",
            **cursor.model_dump(),
        }
        response = requests.get(
            f"{self.email_api_url}/{mailbox}", params=params)
        response.raise_for_status()
        result = ApiResponse[PaginatedResponse[EmailMessageModel]](
            **response.json())
        return result

    def fetch_paginated_promerica_email(
        self,
        mailbox: str,
        start_date: datetime,
        end_date: datetime,
        cursor: CursorModel,
    ) -> ApiResponse[PaginatedResponse[EmailMessageModel]]:
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "senders": "info@promerica.fi.cr",
            "subject": "Comprobante de",
            **cursor.model_dump(),
        }
        response = requests.get(
            f"{self.email_api_url}/{mailbox}", params=params)
        response.raise_for_status()
        result = ApiResponse[PaginatedResponse[EmailMessageModel]](
            **response.json())
        return result
