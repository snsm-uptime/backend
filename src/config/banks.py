

from typing import Optional, Type

from pydantic import BaseModel, ConfigDict

from ..models.enums import Bank
from ..parsers import (BacMessageParser, BaseMessageParser,
                       PromericaMessageParser)


class BankConfig(BaseModel):
    senders: str
    subject: Optional[str]
    parser: Type[BaseMessageParser]

    model_config = ConfigDict(arbitrary_types_allowed=True)


bank_config = {
    Bank.BAC: BankConfig(
        senders="notificacion@notificacionesbaccr.com",
        subject=None,
        parser=BacMessageParser
    ),
    Bank.PROMERICA: BankConfig(
        senders="info@promerica.fi.cr",
        subject="Comprobante de",
        parser=PromericaMessageParser
    )
}
