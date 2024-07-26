from enum import Enum, auto


class Bank(Enum):
    PROMERICA = ("Promerica", "info@promerica.fi.cr")
    BAC = ("BAC", "notificacion@notificacionesbaccr.com")
    SIMAN = ("Siman", "")

    @property
    def name(self):
        return self.value[0]

    @property
    def email(self):
        return self.value[1]

    @classmethod
    def from_email_or_name(cls, identifier: str):
        for bank in cls:
            if bank.name.lower() == identifier.lower() or bank.email.lower() == identifier.lower():
                return bank
        return None


class ExpensePriority(Enum):
    MUST = auto()
    WANT = auto()
    NEED = auto()


class ExpenseType(Enum):
    TAXES = auto()
    GROCERIES = auto()
    EATING_OUT = auto()
    ENTERTAINMENT = auto()
    TRANSPORT = auto()
    SELF_CARE = auto()
    PET = auto()
    GIFT = auto()
