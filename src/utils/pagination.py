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
        return list(chain.from_iterable(data)), execution_time


class ThreadedPaginator(Paginator[T]):
    def __init__(
        self,
        logger: logging.Logger,
        pagination_details: PaginationDetails,
        thread_count: int,
        process_function: Callable[[int], List[T]],
    ):
        super().__init__(logger, pagination_details, process_function)
        self.thread_count = max(1, thread_count)
        self.results = [None] * (
            (self.total_items + self.page_size - 1) // self.page_size
        )

    @timed_operation
    def _paginate(self) -> List[T]:
        total_pages = len(self.results)
        self.info(
            'pagination_details',
            f"Total Documents, Pages: {self.total_items}, {total_pages}"
        )

        if self.thread_count == 1:
            self.logger.info("pagination_mode"
                             "Running in single thread mode.")
            for page in range(1, total_pages + 1):
                self._worker(page, page)
        else:
            self.logger.info("pagination_mode"
                             f"Running in multi-thread mode. ({self.thread_count} threads)")
            pages_per_thread = (
                total_pages + self.thread_count - 1
            ) // self.thread_count
            with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
                for i in range(self.thread_count):
                    start_page = i * pages_per_thread + 1
                    end_page = min(
                        start_page + pages_per_thread - 1, total_pages)
                    executor.submit(self._worker, start_page, end_page)

        return self.results

    def _worker(self, start_page: int, end_page: int):
        for page in range(start_page, end_page + 1):
            result = self.process_function(page)
            if result is None:
                self.logger.error(
                    f"Processed page {page} with skip count {
                        page} and got None."
                )
            else:
                self.results[page - 1] = result
            self.debug('iteration', f"PAGE={page}:CURSOR={page}")
