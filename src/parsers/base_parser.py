from abc import ABC, abstractmethod
from datetime import datetime
from email.message import Message
from logging import getLogger
from typing import Tuple

from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date


class BaseMessageParser(ABC):
    def __init__(self, msg: Message):
        self.msg = msg
        self.logger = getLogger(self.__class__.__name__)
        self._body = self.__parse_body()

    @property
    def body(self) -> str | None:
        return self._body

    def __parse_body(self) -> str | None:
        try:
            if self.msg.is_multipart():
                for part in self.msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = part.get("Content-Disposition")

                    self.logger.debug(f"Part content type: {content_type}")
                    self.logger.debug(
                        f"Part content disposition: {content_disposition}")

                    # Process parts even if Content-Disposition is missing or not an attachment
                    if content_disposition is None or "attachment" not in content_disposition:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            body = payload.decode(charset, errors="replace")
                            if "text/plain" in content_type:
                                return body
                            elif "text/html" in content_type:
                                soup = BeautifulSoup(body, "html.parser")
                                return soup.get_text(separator='\n').strip()
                        else:
                            self.logger.debug(
                                f"No payload to decode in part with content type: {content_type}")
            else:
                content_type = self.msg.get_content_type()
                payload = self.msg.get_payload(decode=True)
                if payload:
                    charset = self.msg.get_content_charset() or "utf-8"
                    body = payload.decode(charset, errors="replace")
                    if "text/plain" in content_type:
                        return body
                    elif "text/html" in content_type:
                        soup = BeautifulSoup(body, "html.parser")
                        return soup.get_text(separator='\n').strip()
                else:
                    self.logger.debug(
                        f"No payload to decode in message with content type: {content_type}")
        except Exception as e:
            self.logger.exception(f"Failed to parse email body: {e}")
            return None
        return None

    @abstractmethod
    def parse_business(self) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def parse_business_type(self) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def parse_value_and_currency(self) -> Tuple[float, str]:
        raise NotImplementedError

    def parse_date(self) -> datetime:
        return parse_date(self.msg.get('date'))
