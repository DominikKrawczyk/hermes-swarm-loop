"""Thread-safe connection pool with PooledConnection wrappers.

acquire() returns a PooledConnection whose .close() returns the
underlying resource to the idle pool.
"""

import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Callable, Generic, List, Optional, Set, TypeVar, Generator

T = TypeVar("T")


class ConnectionClosedError(RuntimeError):
    """Raised when an operation is attempted on a closed pool."""


class ConnectionTimeoutError(TimeoutError):
    """Raised when acquire() times out waiting for a connection."""


@dataclass
class PoolStats:
    """Snapshot of pool state at a point in time."""
    max_size: int = 0
    size: int = 0
    idle: int = 0
    in_use: int = 0
    waits: int = 0
    timeouts: int = 0


class PooledConnection(Generic[T]):
    """A wrapper around a raw connection that tracks pool membership.

    Call ``.close()`` to return the underlying resource to the pool,
    or ``.detach()`` to take ownership and remove it from pool tracking.
    """

    __slots__ = ("resource", "pool", "_closed")

    def __init__(self, resource: T, pool: "ConnectionPool[T]") -> None:
        self.resource = resource
        self.pool = pool
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        """Return the resource to the pool for reuse."""
        if self._closed:
            return
        self._closed = True
        self.pool._release(self)

    def detach(self) -> T:
        """Remove from pool tracking and return the raw resource."""
        self._closed = True
        r = self.resource
        self.pool._discard(self)
        return r

    def __enter__(self) -> T:
        return self.resource

    def __exit__(self, *args) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"PooledConnection(resource={self.resource}, closed={self._closed})"


@dataclass
class ConnectionPool(Generic[T]):
    """A thread-safe pool of reusable connections.

    ``acquire()`` returns a ``PooledConnection`` whose ``.close()``
    returns the underlying resource to the idle pool.

    Test-API affordances:
      ``max_connections``  — alias for ``max_size``
      ``release(conn)``    — put a raw connection back into the pool
      ``available``        — number of idle connections (property)
      ``active``           — number of in-use connections (property)
    """

    factory: Callable[[], T]
    max_size: int
    acquire_timeout: float = 10.0
    validate: Optional[Callable[[T], bool]] = None
    close_fn: Optional[Callable[[T], None]] = None

    # Internal state — _in_use holds strong refs to prevent GC from
    # freeing tracked PooledConnections whose id() would then be reused.
    _pool: list = field(default_factory=list, init=False)          # idle PooledConnections
    _in_use: set = field(default_factory=set, init=False)          # strong refs to in-use PooledConnections
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False)
    _available_event: threading.Event = field(default_factory=threading.Event, init=False)
    _closed: bool = field(default=False, init=False)
    _waits: int = field(default=0, init=False)
    _timeouts: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if self.max_size <= 0:
            raise ValueError(f"max_size must be > 0, got {self.max_size}")
        if self.acquire_timeout <= 0:
            raise ValueError(f"acquire_timeout must be > 0, got {self.acquire_timeout}")

    # ── core properties ───────────────────────────────────────────────

    @property
    def size(self) -> int:
        """Total number of connections (idle + in-use)."""
        return len(self._pool) + len(self._in_use)

    @property
    def idle(self) -> int:
        """Number of idle connections ready for reuse."""
        return len(self._pool)

    @property
    def in_use(self) -> int:
        """Number of connections currently in use."""
        return len(self._in_use)

    @property
    def stats(self) -> PoolStats:
        """Snapshot of current pool statistics."""
        with self._lock:
            return PoolStats(
                max_size=self.max_size,
                size=len(self._pool) + len(self._in_use),
                idle=len(self._pool),
                in_use=len(self._in_use),
                waits=self._waits,
                timeouts=self._timeouts,
            )

    # ── test-API affordances ──────────────────────────────────────────

    @property
    def max_connections(self) -> int:
        """Alias for max_size (test compatibility)."""
        return self.max_size

    @max_connections.setter
    def max_connections(self, value: int) -> None:
        self.max_size = value

    @property
    def available(self) -> int:
        """Alias for idle (test compatibility)."""
        return len(self._pool)

    @property
    def active(self) -> int:
        """Alias for in_use (test compatibility)."""
        return len(self._in_use)

    # ── acquire / release ─────────────────────────────────────────────

    def acquire(self, timeout: Optional[float] = None) -> PooledConnection[T]:
        """Acquire a pooled connection, creating one if necessary.

        Returns a ``PooledConnection`` wrapping the raw resource.
        Call ``.close()`` on the result to return it to the pool.
        """
        deadline = time.monotonic() + (
            timeout if timeout is not None else self.acquire_timeout
        )
        while True:
            with self._lock:
                if self._closed:
                    raise ConnectionClosedError("Pool closed")

                # Try a cached idle connection (validate first)
                while self._pool:
                    c = self._pool.pop()
                    if self._validate_resource(c.resource):
                        self._in_use.add(c)
                        return c
                    self._discard_internal(c)

                # Create new if we're under max_size
                if len(self._pool) + len(self._in_use) < self.max_size:
                    r = self.factory()
                    c = PooledConnection(r, self)
                    self._in_use.add(c)
                    return c

            # At capacity — wait for a release
            self._waits += 1
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self._timeouts += 1
                raise ConnectionTimeoutError(
                    f"Timeout after {timeout or self.acquire_timeout}s"
                )
            self._available_event.wait(timeout=min(remaining, 0.1))
            self._available_event.clear()

    def release(self, conn: T) -> None:
        """Return a raw connection to the pool.

        If *conn* was obtained via ``acquire()`` and is still tracked,
        this is equivalent to calling ``.close()`` on the
        ``PooledConnection``.  The raw resource is wrapped in a fresh
        ``PooledConnection`` and made available for reuse.
        """
        with self._lock:
            self._pool.append(PooledConnection(conn, self))
            self._available_event.set()

    @contextmanager
    def acquire_context(
        self, timeout: Optional[float] = None
    ) -> Generator[T, None, None]:
        """Context manager that yields the raw resource and auto-closes."""
        pooled = self.acquire(timeout)
        try:
            yield pooled.resource
        finally:
            pooled.close()

    # ── pool lifecycle ────────────────────────────────────────────────

    def warm(self, count: int) -> None:
        """Pre-populate the idle pool with *count* connections."""
        if count < 0:
            raise ValueError(f"count must be >= 0, got {count}")
        with self._lock:
            if len(self._pool) + len(self._in_use) + count > self.max_size:
                raise ValueError(
                    f"cannot warm {count}, would exceed {self.max_size}"
                )
            for _ in range(count):
                r = self.factory()
                self._pool.append(PooledConnection(r, self))

    def close(self) -> None:
        """Close the pool and evict all idle connections."""
        with self._lock:
            self._closed = True
            self._evict_all_idle()
            self._available_event.set()

    def close_all(self) -> None:
        """Close and drain every connection (idle + in-use)."""
        with self._lock:
            self._closed = True
            self._evict_all_idle()
            self._in_use.clear()
            self._available_event.set()

    # ── internal helpers ──────────────────────────────────────────────

    def _release(self, conn: PooledConnection) -> None:
        """Internal release — called by PooledConnection.close()."""
        with self._lock:
            self._in_use.discard(conn)
            if self._closed:
                self._discard_internal(conn)
            else:
                self._pool.append(conn)
            self._available_event.set()

    def _discard(self, conn: PooledConnection) -> None:
        """Remove *conn* from the in-use tracking set."""
        with self._lock:
            self._in_use.discard(conn)

    def _validate_resource(self, r: T) -> bool:
        if self.validate is None:
            return True
        try:
            return self.validate(r)
        except Exception:
            return False

    def _discard_internal(self, conn: PooledConnection) -> None:
        if self.close_fn:
            try:
                self.close_fn(conn.resource)
            except Exception:
                pass

    def _evict_all_idle(self) -> None:
        for c in self._pool:
            self._discard_internal(c)
        self._pool.clear()

    # ── dunder ────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return (
            f"ConnectionPool(size={self.size}, idle={self.idle}, "
            f"in_use={self.in_use}, max={self.max_size})"
        )

    def __enter__(self) -> "ConnectionPool[T]":
        return self

    def __exit__(self, *args) -> None:
        self.close()
