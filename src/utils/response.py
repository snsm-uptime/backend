

from http import HTTPStatus

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from ..schemas.api_response import ApiResponse, Meta


def create_exception_response(status_code: HTTPStatus, exception: Exception) -> JSONResponse:
    meta = Meta(status=status_code,
                message='. '.join(exception.args))
    raise JSONResponse(status_code=meta.status,
                       content=jsonable_encoder(meta))


def create_json_response(api_response: ApiResponse) -> JSONResponse:
    return JSONResponse(api_response.meta.status, jsonable_encoder(api_response))
