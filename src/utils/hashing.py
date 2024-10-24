import pickle
import hashlib
from typing import Any

from ..schemas.api_response import PaginationMeta


def hash_any(model: Any) -> str:
    meta_bytes = pickle.dumps(model)
    return hashlib.sha256(meta_bytes).hexdigest()


def hash_pagination_meta(meta: PaginationMeta) -> str:
    """
    Only total_items, page_size and current_page are required
    """
    meta_json = meta.model_dump_json(exclude={
                                     'next_cursor', 'prev_cursor', 'total_pages'})
    # Create SHA256 hash of the JSON string
    return hashlib.sha256(meta_json.encode('utf-8')).hexdigest()
