import logging
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding='utf-8',
        extra="ignore"
    )
    PAGE_SIZE: int = 15
    CACHE_CAPACITY_TRANSACTION_LIST: int = 5
    ENVIRONMENT: Literal['local', 'dev', 'prod'] = 'local'


config = Settings()
