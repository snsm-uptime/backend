import base64
from hashlib import sha256
import json
from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, model_validator

from ..config import config

T = TypeVar('T')


class PaginationMeta(BaseModel):
    total_items: Optional[int] = None
    total_pages: Optional[int] = None
    page_size: Optional[int] = None
    current_page: Optional[int] = None
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None


class Meta(BaseModel):
    status: int
    message: Optional[str] = None
    request_time: float = 0.0


class PaginatedResponse(BaseModel, Generic[T]):
    pagination: Optional[PaginationMeta] = None
    items: Optional[List[T]] = None


class SingleResponse(BaseModel, Generic[T]):
    item: Optional[T] = None


class ApiResponse(BaseModel, Generic[T]):
    meta: Meta
    data: Optional[T] = None


class CursorModel(BaseModel):
    page_size: Optional[int] = Field(
        ..., description="The size of the page to fetch")
    page: Optional[int] = Field(
        ..., description="The current page number")
    cursor: Optional[str] = Field(
        default=None, description="The cursor string for pagination")

    @model_validator(mode='before')
    def initialize_fields(cls, values):
        cursor = values.get('cursor')
        page = values.get('page')
        page_size = values.get('page_size')
        if cursor:
            try:
                cursor_str = base64.urlsafe_b64decode(cursor.encode()).decode()
                data = json.loads(cursor_str)
                cursor_page = data.get('page', 1)
                cursor_page_size = data.get('page_size', config.PAGE_SIZE)
                if not page:
                    values['page'] = cursor_page
                if not page_size:
                    values['page_size'] = cursor_page_size
            except (base64.binascii.Error, json.JSONDecodeError):
                raise ValueError("Invalid cursor format")
        else:
            values['page'] = page if page else 1
            values['page_size'] = page_size if page_size else config.PAGE_SIZE
        return values

    def encode(self) -> str:
        """
        Encode the current page and page_size into a base64 cursor string.

        Returns:
            str: The base64 encoded cursor string.
        """
        cursor_data = {"page": self.page, "page_size": self.page_size}
        cursor_str = json.dumps(cursor_data)
        self.cursor = base64.urlsafe_b64encode(cursor_str.encode()).decode()
        return self.cursor

    @ staticmethod
    def encode_from_dict(page: int, page_size: int) -> str:
        """
        Encode given page and page_size into a base64 cursor string.

        Args:
            page (int): The current page number.
            page_size (int): The size of the page to fetch.

        Returns:
            str: The base64 encoded cursor string.
        """
        cursor_data = {"page": page, "page_size": page_size}
        cursor_str = json.dumps(cursor_data)
        return base64.urlsafe_b64encode(cursor_str.encode()).decode()

    @ staticmethod
    def decode(cursor: str) -> 'CursorModel':
        """
        Decode a base64 cursor string into a CursorModel instance.

        Args:
            cursor (str): The base64 encoded cursor string.

        Returns:
            CursorModel: A CursorModel instance with page and page_size populated.
        """
        try:
            cursor_str = base64.urlsafe_b64decode(cursor.encode()).decode()
            data = json.loads(cursor_str)
            return CursorModel(
                page=data.get('page', None),
                page_size=data.get('page_size', None),
                cursor=cursor
            )
        except (base64.binascii.Error, json.JSONDecodeError) as e:
            raise ValueError("Invalid cursor format") from e


class DateRange(BaseModel):
    start_date: datetime = Field(...,
                                 description="Start date in ISO format (YYYY-MM-DD)")
    end_date: datetime = Field(...,
                               description="End date in ISO format (YYYY-MM-DD)")

    def __str__(self) -> str:
        psd = self.start_date.strftime("%B %d, %Y at %I:%M %p")
        ped = self.end_date.strftime("%B %d, %Y at %I:%M %p")
        return f'{psd} to {ped}'
