from http import HTTPStatus
from logging import getLogger
from typing import Callable, Generic, List, Optional, Type

from sqlalchemy.orm import Session

from email_transaction_extractor.repositories.generic_repository import \
    GenericRepository
from email_transaction_extractor.schemas.api_response import (
    ApiResponse, Meta, PaginatedResponse, PaginationMeta, SingleResponse)
from email_transaction_extractor.typing import (CreateSchemaType, ModelType,
                                                ReturnSchemaType,
                                                UpdateSchemaType)
from email_transaction_extractor.utils.pagination import (decode_cursor,
                                                          encode_cursor)


class GenericService(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ReturnSchemaType]):
    def __init__(self, model: Type[ModelType], create_schema: Type[CreateSchemaType], update_schema: Type[UpdateSchemaType], return_schema: Type[ReturnSchemaType], repository: GenericRepository):
        self.model = model
        self.create_schema = create_schema
        self.update_schema = update_schema
        self.return_schema = return_schema
        self.repository = repository
        self.logger = getLogger(self.__class__.__name__)

    def create(self, obj_in: CreateSchemaType) -> ApiResponse[SingleResponse[ReturnSchemaType]]:
        obj_in_data = obj_in.model_dump()
        db_obj, elapsed_time = self.repository.create(
            self.model(**obj_in_data))
        meta = Meta(status=HTTPStatus.CREATED, request_time=elapsed_time)
        item = self.return_schema.model_validate(db_obj)
        return ApiResponse(meta=meta, data=SingleResponse(item=item))

    def get(self, id: str) -> ApiResponse[SingleResponse[ReturnSchemaType]]:
        db_obj, elapsed_time = self.repository.get(id)
        status = HTTPStatus.OK if db_obj else HTTPStatus.NOT_FOUND
        meta = Meta(status=status, request_time=elapsed_time)
        item = self.return_schema.model_validate(db_obj) if db_obj else None
        return ApiResponse(meta=meta, data=SingleResponse(item=item))

    def get_all(self, ) -> ApiResponse[SingleResponse[List[ReturnSchemaType]]]:
        data, elapsed_time = self.repository.get_all()
        return ApiResponse(meta=Meta(status=HTTPStatus.OK, request_time=elapsed_time), data=data)

    def get_paginated(self, page_size: int, cursor: Optional[str] = None, filter: Optional[Callable[[ModelType], bool]] = None) -> ApiResponse[PaginatedResponse[ReturnSchemaType]]:
        if cursor:
            cursor_data = decode_cursor(cursor)
            if cursor_data is None:
                raise ValueError("Invalid cursor")
            current_page = cursor_data['page']
        else:
            current_page = 1

        total_items, count_elapsed_time = self.repository.count(filter)
        offset = (current_page - 1) * page_size
        db_objs, paginated_elapsed_time = self.repository.get_paginated(
            offset, page_size, filter)

        total_pages = (total_items + page_size - 1) // page_size
        request_time = count_elapsed_time + paginated_elapsed_time

        next_cursor = encode_cursor(
            current_page + 1, page_size) if current_page < total_pages else None
        prev_cursor = encode_cursor(
            current_page - 1, page_size) if current_page > 1 else None

        items = [self.return_schema.model_validate(obj) for obj in db_objs]

        meta = Meta(status=HTTPStatus.OK, request_time=request_time,
                    message="Transactions retrieved successfully")
        pagination = PaginationMeta(
            total_items=total_items,
            total_pages=total_pages,
            page_size=page_size,
            current_page=current_page,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor
        )

        response = ApiResponse(meta=meta, data=PaginatedResponse(
            pagination=pagination, items=items))
        return response

    def update(self, id: str, obj_in: UpdateSchemaType) -> ApiResponse[SingleResponse[ReturnSchemaType]]:
        obj_in_data = obj_in.model_dump()
        db_obj, elapsed_time = self.repository.update(id, obj_in_data)
        status = HTTPStatus.OK if db_obj else HTTPStatus.NOT_FOUND
        meta = Meta(status=status, request_time=elapsed_time)
        item = self.return_schema.model_validate(db_obj) if db_obj else None
        return ApiResponse(data=SingleResponse(meta=meta, item=item))

    def delete(self, id: str) -> ApiResponse[SingleResponse[ReturnSchemaType]]:
        db_obj, elapsed_time = self.repository.delete(id)
        status = HTTPStatus.OK if db_obj else HTTPStatus.NOT_FOUND
        meta = Meta(status=status, request_time=elapsed_time)
        item = self.return_schema.model_validate(db_obj) if db_obj else None
        return ApiResponse(data=SingleResponse(meta=meta, item=item))
