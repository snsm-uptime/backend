from logging import getLogger
from typing import Callable, Generic, List, Optional, Tuple, Type, Union

from fastapi import Query
from sqlalchemy import ColumnElement, select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..schemas.typing import ModelType
from ..utils.decorators import timed_operation


class GenericRepository(Generic[ModelType]):
    def __init__(self, db: Session, model: Type[ModelType]):
        self.db = db
        self.model = model
        self.logger = getLogger(self.__class__.__name__)

    @timed_operation
    def create(self, obj_in: ModelType) -> Tuple[ModelType, float]:
        self.db.add(obj_in)
        try:
            self.db.commit()
            self.db.refresh(obj_in)
            return obj_in
        except IntegrityError as e:
            self.db.rollback()
            raise e

    @timed_operation
    def get(self, id: str) -> Tuple[Optional[ModelType], float]:
        return self.db.query(self.model).filter(self.model.id == id).first()

    @timed_operation
    def get_all(self) -> Tuple[List[ModelType], float]:
        return self.db.query(self.model).all()

    @timed_operation
    def update(self, id: str, obj_in: dict) -> Tuple[Optional[ModelType], float]:
        db_obj = self.get(id)
        if db_obj:
            for key, value in obj_in.items():
                setattr(db_obj, key, value)
            try:
                self.db.commit()
                self.db.refresh(db_obj)
                return db_obj
            except IntegrityError as e:
                self.db.rollback()
                raise e
        return None

    @timed_operation
    def delete(self, id: str) -> Tuple[Optional[ModelType], float]:
        db_obj = self.get(id)
        if db_obj:
            self.db.delete(db_obj)
            try:
                self.db.commit()
                return db_obj
            except IntegrityError as e:
                self.db.rollback()
                raise e
        return None

    @timed_operation
    def get_paginated(
        self, offset: int, limit: int, where: Optional[ColumnElement] = None,
        order_by: Optional[Union[ColumnElement, list[ColumnElement]]] = None
    ) -> Tuple[List[ModelType], float]:
        query = select(self.model)

        if order_by is not None:
            query = query.order_by(*order_by)
        if where is not None:
            query = query.where(where)

        results = self.db.execute(
            query
            .offset(offset)
            .limit(limit)
        ).scalars().all()
        return results

    @timed_operation
    def count(self, where: Optional[ColumnElement] = None) -> Tuple[int, float]:
        query = select(func.count()).select_from(self.model)
        if where is not None:
            query = query.where(where).order_by()
        return self.db.execute(query).scalar_one()
