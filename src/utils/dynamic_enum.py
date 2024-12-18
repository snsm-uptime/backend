from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import select


def generate_dynamic_enum(session: Session, table: type, column: str) -> Enum:
    """
    Generic function to dynamically create a Python Enum from a database column.
    """
    results = session.execute(select(getattr(table, column))).scalars().all()
    return Enum(table.__name__, {value: value for value in results})


def validate_enum_value(value: str, enum: Enum):
    if value not in enum.__members__:
        raise ValueError(f"Invalid value '{value}' for enum '{enum.__name__}'")


def remap_currency_codes(code: str) -> str:
    match code:
        case "ARP":
            return "ARS"
        case "MXP":
            return "MXN"
        case _:
            return code
