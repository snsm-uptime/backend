from sqlalchemy import Column, String, Integer, TIMESTAMP, text
from sqlalchemy.orm import declarative_base

from ._base import Base


class CurrencyTable(Base):
    __tablename__ = 'currencies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(3), unique=True, nullable=False)
    name = Column(String(100), nullable=True)
    symbol = Column(String(5), nullable=True)
    region = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, server_default=text(
        'CURRENT_TIMESTAMP'), nullable=False)
