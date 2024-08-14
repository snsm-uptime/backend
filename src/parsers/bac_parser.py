from email.message import Message
import re
from typing import Tuple
from . import BaseMessageParser


class BacMessageParser(BaseMessageParser):
    def __init__(self, msg: Message):
        self.msg = msg
        super().__init__(msg)

    def parse_business(self) -> str | None:
        regex = re.compile(
            r'Comercio:\s*\r\n(?P<business>.+?)\s*\n', re.DOTALL)
        match = regex.search(self.body)
        return match.group('business').strip() if match else None

    def parse_business_type(self) -> str | None:
        return None

    def parse_value_and_currency(self) -> Tuple[float, str]:
        regex = re.compile(
            r'Monto:\s*(?:\r?\n)?\s*(?P<currency>[A-Z]{3})\s*(?P<value>[\d,]*\.\d{2})'
        )

        match = regex.search(self.body)
        if match:
            currency = match.group('currency').strip()
            value = float(match.group('value').replace(',', ''))
            return value, currency
        return 0.0, ''
