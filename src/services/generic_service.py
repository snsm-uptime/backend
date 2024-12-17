from http import HTTPStatus
from logging import getLogger
from typing import Callable, Generic, List, Optional, Type, Union

from sqlalchemy import ColumnElement

from ..repositories.generic_repository import GenericRepository
from ..schemas.api_response import (ApiResponse, CursorModel, Meta,
                                    PaginatedResponse, PaginationMeta,
                                    SingleResponse)
from ..schemas.typing import (CreateSchemaType, ModelType, ReturnSchemaType,
                              UpdateSchemaType)


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

    def get_all(self) -> ApiResponse[SingleResponse[List[ReturnSchemaType]]]:
        data, elapsed_time = self.repository.get_all()
        items = [self.return_schema.model_validate(obj) for obj in data]
        return ApiResponse(meta=Meta(status=HTTPStatus.OK, request_time=elapsed_time), data=SingleResponse(item=items))

    def get_paginated(self, cursor: CursorModel, filter: Optional[ColumnElement] = None,
                      order_by: Optional[Union[ColumnElement,
                                               list[ColumnElement]]] = None
                      ) -> ApiResponse[PaginatedResponse[ReturnSchemaType]]:
        current_page = cursor.page
        page_size = cursor.page_size

        total_items, count_elapsed_time = self.repository.count(filter)
        offset = (current_page - 1) * page_size
        db_objs, paginated_elapsed_time = self.repository.get_paginated(
            offset, page_size, filter, order_by)

        total_pages = (total_items + page_size - 1) // page_size
        request_time = count_elapsed_time + paginated_elapsed_time

        next_cursor = CursorModel(
            page=current_page + 1, page_size=page_size).encode() if current_page < total_pages else None
        prev_cursor = CursorModel(
            page=current_page - 1, page_size=page_size).encode() if current_page > 1 else None

        items = [self.return_schema.model_validate(obj) for obj in db_objs]

        meta = Meta(status=HTTPStatus.OK, request_time=request_time,
                    message="Transactions retrieved successfully")
        pagination = PaginationMeta(
            total_items=total_items,
            total_pages=total_pages,
            page_size=page_size,
            page=current_page,
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
