from logging import getLogger

import requests

from ..models.enums import Bank

from ..schemas.api_response import DateRange
from ..config import bank_config

from ..schemas import (
    EmailMessageModel,
    ApiResponse,
    CursorModel,
    PaginatedResponse,
)


class EmailReaderService:
    def __init__(self):
        self.email_api_url = "http://email-api:80"
        self.logger = getLogger(__class__.__name__)

    def __fetch_paginated_email_from_bank(
        self,
        mailbox: str,
        date_range: DateRange,
        cursor: CursorModel,
        bank: Bank,
    ) -> ApiResponse[PaginatedResponse[EmailMessageModel]]:
        bank_params = bank_config[bank]

        params = {
            "start_date": date_range.start_date,
            "end_date": date_range.end_date,
            "senders": bank_params.senders,
            **cursor.model_dump(),
        }

        if bank_params.subject:
            params["subject"] = bank_params.subject

        response = requests.get(
            f"{self.email_api_url}/{mailbox}", params=params)
        response.raise_for_status()

        return ApiResponse[PaginatedResponse[EmailMessageModel]](**response.json())

    def fetch_emails_page_from_bank(self, bank: Bank, mailbox: str, date_range: DateRange, page: int, page_size: int) -> ApiResponse[PaginatedResponse[EmailMessageModel]]:
        cursor = CursorModel(page=page, page_size=page_size)
        data = self.__fetch_paginated_email_from_bank(
            bank=bank, mailbox=mailbox, date_range=date_range, cursor=cursor)
        return data
