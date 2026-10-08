"""Bounded byte LRU holding pristine pages, never mutable execution state."""

from collections import OrderedDict
from copy import deepcopy
from typing import Callable, Protocol

from .accounting import Accounting
from .models import JSON, ResidencyEvent
from .serialization import canonical


class ResidencyPolicy(Protocol):
    def admit(self, key: str, size: int, capacity: int) -> bool: ...
    def victim(self, pages: tuple[tuple[str, int], ...]) -> str: ...


class LRUPolicy:
    def admit(self, key: str, size: int, capacity: int) -> bool:
        return size <= capacity

    def victim(self, pages: tuple[tuple[str, int], ...]) -> str:
        return pages[0][0]


class ResidencyCache:
    def __init__(self, capacity_bytes: int = 1_048_576, *, policy: ResidencyPolicy | None = None) -> None:
        self.policy = policy or LRUPolicy()
        if capacity_bytes < 0:
            raise ValueError("cache capacity must be nonnegative")
        self.capacity_bytes = capacity_bytes
        self._pages: OrderedDict[str, tuple[JSON, int]] = OrderedDict()
        self.used_bytes = 0
        self.peak_bytes = 0

    def get(
        self, key: str, accounting: Accounting, emit: Callable[[ResidencyEvent], None]
    ) -> tuple[bool, JSON]:
        if key not in self._pages:
            accounting.add("cache_misses")
            return False, None
        value, size = self._pages[key]
        self._pages.move_to_end(key)
        accounting.add("cache_hits")
        emit(ResidencyEvent(key, "reuse", size, "pristine versioned page reused"))
        return True, deepcopy(value)

    def retain(
        self, key: str, value: JSON, accounting: Accounting, emit: Callable[[ResidencyEvent], None]
    ) -> None:
        size = len(canonical(value).encode("utf-8"))
        if size > self.capacity_bytes or not self.policy.admit(key, size, self.capacity_bytes):
            emit(ResidencyEvent(key, "evict", size, "page exceeds cache byte budget"))
            accounting.add("cache_evictions")
            return
        if key in self._pages:
            _, old_size = self._pages.pop(key)
            self.used_bytes -= old_size
        while self.used_bytes + size > self.capacity_bytes and self._pages:
            victim = self.policy.victim(tuple((k, size) for k, (_, size) in self._pages.items()))
            _, victim_size = self._pages.pop(victim)
            self.used_bytes -= victim_size
            accounting.add("cache_evictions")
            accounting.add("evicted_bytes", victim_size)
            emit(ResidencyEvent(victim, "evict", victim_size, "least recently used; byte budget"))
        self._pages[key] = (deepcopy(value), size)
        self.used_bytes += size
        self.peak_bytes = max(self.peak_bytes, self.used_bytes)
        accounting.add("cache_retains")
        emit(ResidencyEvent(key, "retain", size, "retain pristine page for version-safe replay"))

    def clear(self, accounting: Accounting, emit: Callable[[ResidencyEvent], None]) -> None:
        for key, (_, size) in self._pages.items():
            accounting.add("cache_evictions")
            emit(ResidencyEvent(key, "evict", size, "explicit cache eviction"))
        self._pages.clear()
        self.used_bytes = 0
