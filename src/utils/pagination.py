from itertools import chain
import logging
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Awaitable, Callable, Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationDetails(BaseModel):
    cursor: int = 0
    total_items: int
    page_size: int


class Paginator(ABC, Generic[T]):
    def __init__(
        self,
        logger: logging.Logger,
        pagination_details: PaginationDetails,
        process_function: Callable[[str], Awaitable[List[T]]],
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

    @abstractmethod
    def paginate(self) -> List[T]:
        raise NotImplementedError

    def __call__(self) -> List[T]:
        data = self.paginate()
        return list(chain.from_iterable(data))
        return []


class ThreadedPaginator(Paginator[T]):
    def __init__(
        self,
        logger: logging.Logger,
        pagination_details: PaginationDetails,
        thread_count: int,
        process_function: Callable[[str], List[T]],
    ):
        super().__init__(logger, pagination_details, process_function)
        self.thread_count = max(1, thread_count)
        self.results = [None] * (
            (self.total_items + self.page_size - 1) // self.page_size
        )

    def paginate(self) -> List[T]:
        total_pages = (self.total_items + self.page_size - 1) // self.page_size
        self.logger.info(
            f"[THREAD PAGINATOR] Total Documents, Pages: {self.total_items}, {total_pages}"
        )

        if self.thread_count == 1:
            self.logger.info("[THREAD PAGINATOR] Running in single thread mode.")
            for page in range(1, total_pages + 1):
                self._worker(page, page)
        else:
            self.logger.info(
                f"[THREAD PAGINATOR] Running in multi-thread mode. ({self.thread_count} threads)"
            )
            pages_per_thread = (
                total_pages + self.thread_count - 1
            ) // self.thread_count
            with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
                for i in range(self.thread_count):
                    start_page = i * pages_per_thread + 1
                    end_page = min(start_page + pages_per_thread - 1, total_pages)
                    executor.submit(self._worker, start_page, end_page)

        return self.results

    def log_label(self, suffix: str) -> str:
        return f"[THREADED PAGINATOR:{suffix}]" if suffix else "[THREADED PAGINATOR]"

    def _worker(self, start_page: int, end_page: int):
        for page in range(start_page, end_page + 1):
            skip_count = (page - 1) * self.page_size
            result = self.process_function(skip_count)
            if result is None:
                self.logger.error(
                    f"{self.log_label(self.process_function.__name__)} Processed page {page} with skip count {skip_count} and got None."
                )
            else:
                self.results[page - 1] = result
            message = self.log_label(f"PAGE={page}:CURSOR={skip_count}")
            self.logger.debug(message)
