from typing import Callable, Generic, List, Optional, Tuple, Type

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..schemas.typing import ModelType
from ..utils.decorators import timed_operation


class GenericRepository(Generic[ModelType]):
    def __init__(self, db: Session, model: Type[ModelType]):
        self.db = db
        self.model = model

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
    def get_paginated(self, offset: int, limit: int, filter: Optional[Callable[[ModelType], bool]] = None) -> Tuple[List[ModelType], float]:
        query = self.db.query(self.model)
        if filter is not None:
            query = query.filter(filter)
        return query.offset(offset).limit(limit).all()

    @timed_operation
    def count(self, filter: Optional[Callable[[ModelType], bool]] = None) -> Tuple[int, float]:
        query = self.db.query(self.model)
        if filter is not None:
            query = query.filter(filter)
        return query.count()
