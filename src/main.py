from http import HTTPStatus
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .routers.transactions import router as TransactionRouter

from .models import PydanticValidationError

app = FastAPI()


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

app.include_router(TransactionRouter)
