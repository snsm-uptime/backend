import pickle
from datetime import timedelta
from logging import getLogger
from typing import List, Optional

from pymemcache.client.base import Client

from ..schemas import TransactionCreate, TransactionsPageResponse
from ..schemas.api_response import PaginationMeta
from ..utils import hash_pagination_meta


class MemcacheService:
    def __init__(self, host: str = 'localhost', port: int = 11211):
        self.client = Client((host, port))
        self.logger = getLogger(MemcacheService.__name__)

    def set_transactions(self, data: TransactionsPageResponse, ttl: Optional[timedelta] = None):
        """
        Store a list of TransactionCreate objects in Memcached with optional expiration.
        """
        try:
            # Serialize the transactions list into a pickle object before storing
            transactions_data = pickle.dumps(data.transactions)
            key = hash_pagination_meta(data.pagination_meta)
            if ttl:
                self.client.set(key, transactions_data,
                                expire=int(ttl.total_seconds()))
            else:
                self.client.set(key, transactions_data)
        except Exception as e:
            self.logger.error(f"Error setting transactions in cache: {e}")

    def get_transactions(self, pagination_details: PaginationMeta) -> Optional[List[TransactionCreate]]:
        """
        Retrieve a list of TransactionCreate objects from Memcached.

        Args:
            key (str): The key used to fetch the data.

        Returns:
            Optional[List[TransactionCreate]]: The list of transactions or None if not found.
        """
        try:
            # Retrieve and deserialize the data from cache
            cached_data = self.client.get(
                hash_pagination_meta(pagination_details))
            if cached_data:
                return pickle.loads(cached_data)
            return None
        except Exception as e:
            print(f"Error getting transactions from cache: {e}")
            return None

    def delete(self, key: str):
        """
        Delete a key from Memcached.

        Args:
            key (str): The key to delete from cache.
        """
        try:
            self.client.delete(key)
        except Exception as e:
            print(f"Error deleting key from cache: {e}")

    def clear_cache(self):
        """
        Clear all the keys in Memcached.
        """
        try:
            self.client.flush_all()
        except Exception as e:
            print(f"Error clearing cache: {e}")
