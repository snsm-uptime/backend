from typing import Callable, TypeAlias
from datetime import datetime

# Importing the relevant types
from .schemas import ApiResponse, PaginatedResponse, EmailMessageModel, CursorModel

# Define the custom type
EmailFetcher: TypeAlias = Callable[
    [str, datetime, datetime, CursorModel],
    ApiResponse[PaginatedResponse[EmailMessageModel]],
]
