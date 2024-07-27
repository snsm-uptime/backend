import logging
import time
from functools import wraps
from http import HTTPStatus
from typing import Callable, Tuple, TypeVar

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from ..schemas import ApiResponse, Meta

logger = logging.getLogger(__name__)

T = TypeVar('T')


def timed_operation(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    def wrapper(*args, **kwargs) -> Tuple[T, float]:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.debug(f"{func.__name__} took {elapsed_time:.4f} seconds")
        return result, elapsed_time
    return wrapper


def catch_standard_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            status = HTTPStatus.BAD_REQUEST
            return JSONResponse(
                status_code=status,
                content=jsonable_encoder(ApiResponse(
                    meta=Meta(
                        status_code=status,
                        message='.\n'.join([err.get('msg')
                                           for err in e.errors()])
                    )
                )))
        except Exception as e:
            status = HTTPStatus.INTERNAL_SERVER_ERROR
            return JSONResponse(
                status_code=status,
                content=jsonable_encoder(ApiResponse(
                    meta=Meta(
                        status_code=status,
                        message='.\n'.join([str(err) for err in e.args])
                    )
                )))
    return wrapper
