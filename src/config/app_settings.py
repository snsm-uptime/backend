from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding='utf-8',
        extra="ignore"
    )
    DATABASE_URL: str
    EMAIL_PROCESSING_THREADS: int
    CACHE_CAPACITY_TRANSACTION_LIST: int = 5
    ENVIRONMENT: Literal['local', 'development', 'production'] = 'local'
    MAILBOX: str = 'inbox'
    PAGE_SIZE: int = 15


config = Settings()
