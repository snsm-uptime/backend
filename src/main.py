from http import HTTPStatus
from logging import getLogger
from typing import Literal, Optional
from fastapi import Depends, FastAPI, Path, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import requests

from .models import ApiResponse, CursorModel, DateRange, Meta, PaginatedResponse, EmailMessageModel, PydanticValidationError

app = FastAPI()

# URL of the first FastAPI service
email_api_url = "http://email-reader:80"


class EmailReaderService:
    def __init__(self):
        self.logger = getLogger(__class__.__name__)

    def fetch_paginated_bac_email(self, mailbox: str, start_date: str, end_date: str, cursor: CursorModel) -> ApiResponse[PaginatedResponse[EmailMessageModel]]:
        try:
            params = {
                "start_date": start_date,
                "end_date": end_date,
                "senders": "notificacion@notificacionesbaccr.com",
                **cursor.model_dump()
            }
            response = requests.get(
                f"{email_api_url}/{mailbox}", params=params)
            response.raise_for_status()
            return ApiResponse(**response.json())
        except requests.RequestException as e:
            meta = Meta(status=HTTPStatus.INTERNAL_SERVER_ERROR,
                        message='. '.join(e.args))
            raise JSONResponse(status_code=meta.status,
                               content=jsonable_encoder(meta))

    def fetch_paginated_promerica_email(self, mailbox: str, start_date: str, end_date: str,
                                        cursor: CursorModel) -> ApiResponse[PaginatedResponse[EmailMessageModel]]:
        try:
            params = {
                "start_date": start_date,
                "end_date": end_date,
                "senders": "info@promerica.fi.cr",
                "subject": "Comprobante",
                **cursor.model_dump()
            }
            response = requests.get(
                f"{email_api_url}/{mailbox}", params=params)
            response.raise_for_status()
            return ApiResponse[PaginatedResponse[EmailMessageModel]](**response.json())
        except requests.RequestException as e:
            meta = Meta(status=HTTPStatus.INTERNAL_SERVER_ERROR,
                        message='. '.join(e.args))
            raise JSONResponse(status_code=meta.status,
                               content=jsonable_encoder(meta))

    def get_paginated_promerica_transactions(self, mailbox: str, start_date: str, end_date: str,
                                             cursor: CursorModel) -> ApiResponse[PaginatedResponse[EmailMessageModel]]:
        email_response = self.fetch_paginated_promerica_email(
            mailbox, start_date, end_date, cursor)
        for email in email_response.data.items:
            # TODO: Transform email to Transaction using the corresponding parser
            ...
        return email_response


@app.exception_handler(RequestValidationError)
async def custom_request_validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    custom_errors = [
        str(PydanticValidationError(
            field=".".join(map(str, error.get("loc"))),
            message=error.get("msg"),
            error=error.get("ctx", {}).get("error"),
            input=error.get('input')
        ))
        for error in errors
    ]
    meta = Meta(
        status=HTTPStatus.UNPROCESSABLE_ENTITY,
        message='.\n'.join(custom_errors),
        request_time=0.0
    )

    return JSONResponse(status_code=meta.status, content={"meta": meta.model_dump()})


@app.get("/emails/{mailbox}/{bank}/transactions", response_model=ApiResponse[PaginatedResponse[EmailMessageModel]])
def get_transactions_from_bank(
    mailbox: str = Path(..., description="Mailbox to get the data from"),
    bank: Literal['bac', 'promerica'] = Path(
        ..., description="Bank to process transactions from"),
    date_range: DateRange = Depends(),
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    page: Optional[int] = Query(None, description="Current page"),
    page_size: Optional[int] = Query(
        None, description="Number of items per page"),
):
    cursor = CursorModel(page=page, page_size=page_size, cursor=cursor)
    service = EmailReaderService()
    emails: Optional[ApiResponse] = None
    match bank:
        case x if x == 'promerica':
            emails = service.fetch_paginated_promerica_email(
                mailbox, date_range.start_date, date_range.end_date, cursor)
        case x if x == 'bac':
            emails = service.fetch_paginated_bac_email(
                mailbox, date_range.start_date, date_range.end_date, cursor)
    return JSONResponse(status_code=emails.meta.status, content=jsonable_encoder(emails))
