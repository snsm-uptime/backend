from itertools import chain
import logging
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Awaitable, Callable, Generic, List, Literal, Optional, Tuple, TypeVar

from pydantic import BaseModel

from ..utils.decorators import timed_operation

T = TypeVar("T")


class PaginationDetails(BaseModel):
    total_items: int
    page_size: int


class Paginator(ABC, Generic[T]):
    def __init__(
        self,
        logger: logging.Logger,
        pagination_details: PaginationDetails,
        process_function: Callable[[int], Awaitable[List[T]]],
    ):
        self.total_items = pagination_details.total_items
        self.page_size = pagination_details.page_size
        self.process_function = process_function
        self.__logger = logger
        self.results: List[Optional[T]] = []
        logger.info(f"TOTAL_ITEMS is {self.total_items}")

    @property
    def logger(self) -> logging.Logger:
        return self.__logger

    def debug(self, label: Literal['iteration'], msg: str):
        return self.logger.debug(f'[{label.upper()}] {msg}')

    def info(self, label: Literal['pagination_details', 'pagination_mode'], msg: str):
        return self.logger.info(f'[{label.upper()}] {msg}')

    @abstractmethod
    def _paginate(self) -> List[T]:
        raise NotImplementedError

    def __call__(self) -> Tuple[List[T], float]:
        data, execution_time = self._paginate()
        if isinstance(data[0], list):
            return list(chain.from_iterable(data)), execution_time
        else:
            return data, execution_time


class ThreadedPaginator(Paginator[T]):
    def __init__(
        self,
        logger: logging.Logger,
        pagination_details: PaginationDetails,
        thread_count: int,
        process_function: Callable[[int], List[T]],
        first_result: Optional[T] = None
    ):
        super().__init__(logger, pagination_details, process_function)
        self.thread_count = max(1, thread_count)
        self.first_result = first_result
        # Initialize results list with the correct length based on total pages
        self.results = [None] * (
            (self.total_items + self.page_size - 1) // self.page_size
        )

        if self.first_result:
            self.results[0] = self.first_result

    @timed_operation
    def _paginate(self) -> List[T]:
        total_pages = len(self.results)
        self.info(
            'pagination_details',
            f"Total Documents, Pages: {self.total_items}, {total_pages}"
        )

        # Adjust the page range to skip the first page if already provided
        # Start from page 2 if first result is available
        start_page = 2 if self.first_result else 1

        if self.thread_count == 1:
            self.logger.info("pagination_mode"
                             "Running in single-thread mode.")
            for page in range(start_page, total_pages + 1):
                self._worker(page, page)
        else:
            self.logger.info("pagination_mode"
                             f"Running in multi-thread mode. ({self.thread_count} threads)")
            pages_per_thread = (
                total_pages + self.thread_count - 1
            ) // self.thread_count
            with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
                for i in range(self.thread_count):
                    # Calculate starting and ending pages, skipping the first page if already provided
                    start_page_thread = max(
                        i * pages_per_thread + 1, start_page)
                    end_page_thread = min(
                        start_page_thread + pages_per_thread - 1, total_pages)
                    executor.submit(
                        self._worker, start_page_thread, end_page_thread)

        return self.results

    def _worker(self, start_page: int, end_page: int):
        for page in range(start_page, end_page + 1):
            if page == 1 and self.first_result is not None:
                continue  # Skip the first page if first_result is already set

            result = self.process_function(page)
            if result is None:
                self.logger.error(
                    f"Processed page {page} with skip count {
                        page} and got None."
                )
            else:
                self.results[page - 1] = result
            self.debug('iteration', f"PAGE={page}:CURSOR={page}")
