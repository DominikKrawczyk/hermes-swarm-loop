
import heapq
import threading
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")

@dataclass(order=True)
class PriorityItem(Generic[T]):
    priority: int | float = field(compare=True)
    sequence: int = field(compare=True)
    item: Any = field(compare=False, repr=True)
    timestamp: float = field(default_factory=time.monotonic, compare=True)
    metadata: dict[str, Any] = field(default_factory=dict, compare=False, repr=False)
    def __repr__(self): return f"PriorityItem(priority={self.priority}, item={self.item})"

@dataclass
class PriorityQueueStats:
    size: int = 0
    priority_count: int = 0
    min_priority: float | None = None
    max_priority: float | None = None
    total_put: int = 0
    total_get: int = 0

@dataclass
class PriorityQueue(Generic[T]):
    maxsize: int = 0
    default_priority: int | float = 0
    _heap: list = field(default_factory=list, init=False)
    _sequence: int = field(default=0, init=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False)
    _total_put: int = field(default=0, init=False)
    _total_get: int = field(default=0, init=False)

    def __post_init__(self):
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)

    @property
    def size(self): return len(self._heap)
    def __len__(self): return self.size
    def full(self):
        if self.maxsize <= 0: return False
        with self._lock: return len(self._heap) >= self.maxsize
    def empty(self):
        with self._lock: return len(self._heap) == 0

    def put(self, item, priority=None, metadata=None, block=True, timeout=None):
        if priority is None: priority = self.default_priority
        # Negate priority so higher user-priority = smaller heap-key = popped first
        pitem = PriorityItem(priority=-priority, sequence=self._sequence, item=item, metadata=metadata or {})
        with self._not_full:
            if self.maxsize > 0:
                if not block:
                    if len(self._heap) >= self.maxsize: raise ValueError("Queue full")
                else:
                    deadline = None if timeout is None else time.monotonic() + timeout
                    while len(self._heap) >= self.maxsize:
                        remaining = deadline - time.monotonic() if deadline else None
                        if remaining is not None and remaining <= 0: raise ValueError(f"Timeout {timeout}s")
                        self._not_full.wait(timeout=remaining)
            self._sequence += 1
            heapq.heappush(self._heap, pitem)
            self._total_put += 1
            self._not_empty.notify()

    def get(self, block=True, timeout=None):
        with self._not_empty:
            if not block:
                if not self._heap: raise ValueError("Queue empty")
            else:
                deadline = None if timeout is None else time.monotonic() + timeout
                while not self._heap:
                    remaining = deadline - time.monotonic() if deadline else None
                    if remaining is not None and remaining <= 0: raise ValueError(f"Timeout {timeout}s")
                    self._not_empty.wait(timeout=remaining)
            pitem = heapq.heappop(self._heap)
            self._total_get += 1
            self._not_full.notify()
            return pitem.item

    def get_with_priority(self, block=True, timeout=None):
        with self._not_empty:
            if not block:
                if not self._heap: raise ValueError("Queue empty")
            else:
                deadline = None if timeout is None else time.monotonic() + timeout
                while not self._heap:
                    remaining = deadline - time.monotonic() if deadline else None
                    if remaining is not None and remaining <= 0: raise ValueError(f"Timeout {timeout}s")
                    self._not_empty.wait(timeout=remaining)
            pitem = heapq.heappop(self._heap)
            self._total_get += 1
            self._not_full.notify()
            return pitem

    # -- Test-compatibility aliases --------------------------------------------

    def push(self, item, priority=None):
        """Test-compatible alias for put()."""
        return self.put(item, priority=priority)

    def pop(self):
        """Test-compatible alias for non-blocking get() that returns None on empty."""
        with self._not_empty:
            if not self._heap:
                return None
            pitem = heapq.heappop(self._heap)
            self._total_get += 1
            self._not_full.notify()
            return pitem.item

    @property
    def is_empty(self) -> bool:
        """Test-compatible property for empty check."""
        return not self._heap

    def peek(self):
        with self._lock: return self._heap[0].item if self._heap else None

    def peek_with_priority(self):
        with self._lock: return self._heap[0] if self._heap else None

    def remove(self, item):
        with self._lock:
            for i, p in enumerate(self._heap):
                if p.item is item or p.item == item:
                    last = self._heap.pop()
                    if i < len(self._heap):
                        self._heap[i] = last
                        heapq.heapify(self._heap)
                    self._total_get += 1
                    self._not_full.notify()
                    return True
            return False

    def clear(self):
        with self._lock:
            self._heap.clear()
            self._not_full.notify_all()

    def priorities(self) -> Sequence[int | float]:
        with self._lock: return sorted({-p.priority for p in self._heap})

    def items_by_priority(self, priority):
        with self._lock: return [p.item for p in sorted(self._heap, key=lambda p: p.sequence) if -p.priority == priority]

    @property
    def stats(self) -> PriorityQueueStats:
        with self._lock:
            if not self._heap: return PriorityQueueStats(total_put=self._total_put, total_get=self._total_get)
            p = {-pi.priority for pi in self._heap}
            return PriorityQueueStats(size=len(self._heap), priority_count=len(p), min_priority=min(p), max_priority=max(p), total_put=self._total_put, total_get=self._total_get)

    def __iter__(self):
        with self._lock: snapshot = list(self._heap)
        for p in snapshot: yield p.item
    def qsize(self): return self.size
    def __repr__(self):
        with self._lock: return f"PriorityQueue(size={len(self._heap)}, maxsize={self.maxsize})"
