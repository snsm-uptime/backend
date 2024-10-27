from abc import ABC, abstractmethod
from logging import getLogger
from typing import Tuple

from ..schemas.email import EmailMessageModel


class BaseMessageParser(ABC):
    def __init__(self, msg: EmailMessageModel):
        self.msg = msg
        self.logger = getLogger(self.__class__.__name__)

    @property
    def body(self) -> str:
        return self.msg.body

    @abstractmethod
    def parse_business(self) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def parse_business_type(self) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def parse_value_and_currency(self) -> Tuple[float, str]:
        raise NotImplementedError
