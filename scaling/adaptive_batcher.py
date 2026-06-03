
import threading
import time
from collections import deque
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class Batch(Generic[T]):
    items: Sequence[T]
    created_at: float = field(default_factory=time.monotonic)
    @property
    def size(self) -> int: return len(self.items)
    def __repr__(self): return f"Batch(size={self.size}, created_at={self.created_at:.3f})"


@dataclass
class AdaptiveBatcher(Generic[T]):
    batch_size: int = 1
    min_batch: int = 1
    max_batch: int = 10
    target_latency_ms: float = 1000
    scale_up_threshold: float = 0.8
    interval: float = 0.1

    _buffer: deque = field(default_factory=deque, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    _new_item_event: threading.Event = field(default_factory=threading.Event, init=False)
    _closed: bool = field(default=False, init=False)
    _flush_hook: Callable[[Batch[T]], None] | None = field(default=None, init=False)

    def __post_init__(self):
        if self.batch_size <= 0:
            raise ValueError(f"batch_size must be > 0, got {self.batch_size}")
        if self.min_batch <= 0:
            raise ValueError(f"min_batch must be > 0, got {self.min_batch}")
        if self.max_batch < self.min_batch:
            raise ValueError(
                f"max_batch ({self.max_batch}) must be >= min_batch ({self.min_batch})"
            )
        if self.target_latency_ms <= 0:
            raise ValueError(
                f"target_latency_ms must be > 0, got {self.target_latency_ms}"
            )
        if not (0 < self.scale_up_threshold <= 1):
            raise ValueError(
                f"scale_up_threshold must be in (0, 1], got {self.scale_up_threshold}"
            )
        if self.interval <= 0:
            raise ValueError(f"interval must be > 0, got {self.interval}")

        # Clamp initial batch_size so it respects [min_batch, max_batch]
        if self.batch_size < self.min_batch:
            self.batch_size = self.min_batch
        elif self.batch_size > self.max_batch:
            self.batch_size = self.max_batch

    # ── Public API ──────────────────────────────────────────────

    @property
    def current_batch_size(self) -> int:
        """Alias for batch_size — the currently configured batch size."""
        return self.batch_size

    @current_batch_size.setter
    def current_batch_size(self, value: int) -> None:
        clamped = max(self.min_batch, min(value, self.max_batch))
        with self._lock:
            self.batch_size = clamped

    @property
    def buffer(self) -> Sequence[T]:
        with self._lock:
            return list(self._buffer)

    @property
    def buffer_size(self) -> int:
        with self._lock:
            return len(self._buffer)

    def record_latency(self, ms: float, concurrency_ratio: float) -> None:
        """Adjust batch size based on observed latency.

        When observed latency is below ``target_latency_ms * scale_up_threshold``,
        the batch size grows by 1 (capped at ``max_batch``).  When latency is
        above ``target_latency_ms``, the batch size shrinks by 1 (floored at
        ``min_batch``).  The *concurrency_ratio* parameter is accepted for future
        use but does not affect the current algorithm.
        """
        with self._lock:
            if ms < self.target_latency_ms * self.scale_up_threshold:
                self.batch_size = min(self.batch_size + 1, self.max_batch)
            elif ms > self.target_latency_ms:
                self.batch_size = max(self.batch_size - 1, self.min_batch)

    def reset(self) -> None:
        """Reset batch size to ``min_batch`` and clear pending items."""
        with self._lock:
            self.batch_size = self.min_batch
            self._buffer.clear()
            self._new_item_event.clear()

    def add(self, item: T) -> None:
        with self._lock:
            if self._closed:
                raise RuntimeError("batcher closed")
            self._buffer.append(item)
            if len(self._buffer) >= self.batch_size:
                self._new_item_event.set()

    def extend(self, items: Sequence[T]) -> None:
        with self._lock:
            if self._closed:
                raise RuntimeError("batcher closed")
            self._buffer.extend(items)
            if len(self._buffer) >= self.batch_size:
                self._new_item_event.set()

    def flush(self) -> Batch[T] | None:
        with self._lock:
            if not self._buffer:
                return None
            items = list(self._buffer)
            self._buffer.clear()
            self._new_item_event.clear()
        b = Batch(items=items)
        if self._flush_hook:
            self._flush_hook(b)
        return b

    def close(self) -> Batch[T] | None:
        with self._lock:
            self._closed = True
            self._new_item_event.set()
        return self.flush()

    def set_batch_size(self, size: int) -> None:
        """Manually override the batch size (clamped to [min_batch, max_batch])."""
        if size <= 0:
            raise ValueError(f"batch_size must be > 0, got {size}")
        clamped = max(self.min_batch, min(size, self.max_batch))
        with self._lock:
            self.batch_size = clamped
            if len(self._buffer) >= clamped:
                self._new_item_event.set()

    def set_interval(self, interval: float):
        if interval <= 0:
            raise ValueError(f"interval must be > 0, got {interval}")
        with self._lock:
            self.interval = interval

    def on_flush(self, hook):
        self._flush_hook = hook

    # ── Iteration ───────────────────────────────────────────────

    def __iter__(self) -> Iterator[Batch[T]]:
        return self._generator()

    def _generator(self) -> Iterator[Batch[T]]:
        while True:
            with self._lock:
                closed = self._closed
                buf_len = len(self._buffer)
            if closed and buf_len == 0:
                return
            if not closed and buf_len == 0:
                self._new_item_event.wait(timeout=self.interval)
                self._new_item_event.clear()
                continue
            deadline = time.monotonic() + self.interval
            while not self._new_item_event.is_set():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                self._new_item_event.wait(timeout=min(remaining, 0.05))
            self._new_item_event.clear()
            batch = self.flush()
            if batch is not None:
                yield batch

    # ── repr / context manager ──────────────────────────────────

    def __repr__(self):
        return (
            f"AdaptiveBatcher(batch_size={self.batch_size}, min_batch={self.min_batch}, "
            f"max_batch={self.max_batch}, interval={self.interval}, "
            f"buffered={self.buffer_size})"
        )

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
