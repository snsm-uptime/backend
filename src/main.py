import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from requests import RequestException

from .config.app_settings import config
from .models import PydanticValidationError
from .routers import TransactionRouter, CurrencyRouter
from .utils.logging import configure_root_logger
from .utils.response import create_exception_response
from fastapi.middleware.cors import CORSMiddleware

configure_root_logger(
    log_level=logging.INFO if config.ENVIRONMENT == 'production' else logging.DEBUG)

app = FastAPI(redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def custom_request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    errors = exc.errors()
    custom_errors = ", ".join(
        [
            str(
                PydanticValidationError(
                    field=".".join(map(str, error.get("loc"))),
                    message=error.get("msg"),
                    error=error.get("ctx", {}).get("error"),
                    input=error.get("input"),
                )
            )
            for error in errors
        ]
    )
    return create_exception_response(
        HTTPStatus.UNPROCESSABLE_ENTITY, ValueError(custom_errors)
    )


@app.exception_handler(RequestException)
async def requests_exception_handler(request: Request, exc: RequestException):
    msg = jsonable_encoder(request.json())
    return create_exception_response(HTTPStatus.INTERNAL_SERVER_ERROR, ValueError(msg))


app.include_router(TransactionRouter, prefix="/v1")
app.include_router(CurrencyRouter, prefix="/v1")
