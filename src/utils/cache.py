from typing import Generic, Optional, OrderedDict, TypeVar

T = TypeVar('T')


class LRUCache(Generic[T]):
    def __init__(self, capacity: int):
        self.cache: OrderedDict[str, T] = OrderedDict()
        self.capacity = capacity

    def get(self, key: str) -> Optional[T]:
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, key: str, value: T) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
