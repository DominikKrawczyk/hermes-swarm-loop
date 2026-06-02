import threading
import time
from collections.abc import Generator
from contextlib import contextmanager


class TokenBucket:
    """TokenBucket rate limiter with discrete-interval refill, thread safety.

    Supports continuous refill (legacy, refill_interval_ms=0) and
    discrete-interval refill (refill_interval_ms > 0).

    Parameters
    ----------
    rate : float
        Token refill rate (tokens per second, or per refill-interval group
        when refill_interval_ms > 0).
    capacity : float, optional
        Maximum burst capacity.  Mutually exclusive with *burst*.
    burst : float, optional
        Alias for *capacity*.  Mutually exclusive with *capacity*.
    refill_interval_ms : float, default 0
        If > 0, tokens are refilled in discrete chunks every this many
        milliseconds instead of continuously.  Each chunk adds
        ``rate * (refill_interval_ms / 1000)`` tokens.
    """

    def __init__(
        self,
        rate: float,
        capacity: float | None = None,
        *,
        burst: float | None = None,
        refill_interval_ms: float = 0,
    ):
        if rate <= 0:
            raise ValueError(f"rate must be > 0, got {rate}")

        if burst is not None and capacity is not None:
            raise ValueError("Cannot specify both burst and capacity")
        if burst is not None:
            capacity = burst
        if capacity is None:
            capacity = 1.0
        if capacity <= 0:
            raise ValueError(f"capacity/burst must be > 0, got {capacity}")

        self.rate = float(rate)
        self.capacity = float(capacity)
        self.burst = self.capacity  # alias
        self.refill_interval_ms = float(refill_interval_ms)
        self._tokens = self.capacity
        self._last_refill = time.monotonic()
        self._lock = threading.RLock()

    # ── Properties ──────────────────────────────────────────────────────

    @property
    def tokens(self) -> float:
        with self._lock:
            self._refill()
            return self._tokens

    @property
    def available(self) -> float:
        """Current available tokens (alias for ``tokens``)."""
        return self.tokens

    @property
    def available_tokens(self) -> float:
        """Current available tokens (alias for ``available``)."""
        return self.available

    # ── Public methods ──────────────────────────────────────────────────

    def consume(
        self,
        tokens: float = 1.0,
        block: bool = True,
        timeout: float | None = None,
    ) -> bool:
        """Consume *tokens* from the bucket.

        Parameters
        ----------
        tokens : float
            Number of tokens to consume (must be > 0 and <= capacity).
        block : bool
            If True, block until tokens are available (or *timeout* elapses).
            If False, return immediately.
        timeout : float or None
            Maximum seconds to block.  None = block forever.

        Returns
        -------
        bool
            True if tokens were consumed, False if not (exhausted / timeout).
        """
        if tokens <= 0:
            raise ValueError(f"tokens must be > 0, got {tokens}")
        if tokens > self.capacity:
            raise ValueError(
                f"requested {tokens} exceeds capacity {self.capacity}"
            )
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True
            if not block:
                return False
            if deadline is not None and time.monotonic() >= deadline:
                return False
            time.sleep(min(0.001, 1.0 / self.rate if self.rate > 0 else 0.001))

    def consume_or_wait(
        self, tokens: float = 1.0, timeout: float | None = None
    ) -> bool:
        """Consume *tokens*, blocking if necessary.

        Convenience wrapper around ``consume(tokens, block=True, timeout=timeout)``.

        Returns
        -------
        bool
            True if tokens were consumed, False on timeout.
        """
        return self.consume(tokens, block=True, timeout=timeout)

    def acquire(
        self, tokens: float = 1.0, timeout: float | None = None
    ) -> bool:
        """Alias for ``consume(tokens, block=True, timeout=timeout)``."""
        return self.consume(tokens, True, timeout)

    @contextmanager
    def acquire_context(
        self, tokens: float = 1.0, timeout: float | None = None
    ) -> Generator[bool, None, None]:
        """Context manager that acquires *tokens* on entry."""
        ok = self.consume(tokens, True, timeout)
        try:
            yield ok
        finally:
            pass

    def reset(self) -> None:
        """Restore the bucket to full capacity."""
        with self._lock:
            self._tokens = self.capacity
            self._last_refill = time.monotonic()

    def set_rate(self, rate: float) -> None:
        """Change the refill rate (tokens/sec)."""
        if rate <= 0:
            raise ValueError(f"rate must be > 0, got {rate}")
        with self._lock:
            self._refill()
            self.rate = rate

    def set_capacity(self, capacity: float) -> None:
        """Change the capacity (max burst), trimming excess tokens."""
        if capacity <= 0:
            raise ValueError(f"capacity must be > 0, got {capacity}")
        with self._lock:
            self._refill()
            self.capacity = capacity
            self.burst = capacity  # keep alias in sync
            self._tokens = min(self._tokens, self.capacity)

    # ── Internal refill ─────────────────────────────────────────────────

    def _refill(self) -> None:
        """Refill tokens based on elapsed time.

        * When ``refill_interval_ms == 0`` (default / legacy) tokens are
          refilled continuously: ``tokens += elapsed * rate``.
        * When ``refill_interval_ms > 0`` tokens are refilled in discrete
          chunks every interval: each chunk adds
          ``rate * (refill_interval_ms / 1000)`` tokens.
        """
        now = time.monotonic()
        if self.refill_interval_ms > 0:
            interval_sec = self.refill_interval_ms / 1000.0
            tokens_per_interval = self.rate * interval_sec
            elapsed = now - self._last_refill
            if elapsed >= interval_sec:
                intervals = int(elapsed // interval_sec)
                if intervals > 0:
                    self._tokens = min(
                        self.capacity,
                        self._tokens + intervals * tokens_per_interval,
                    )
                    self._last_refill += intervals * interval_sec
        else:
            # Continuous refill (legacy)
            elapsed = now - self._last_refill
            self._tokens = min(
                self.capacity, self._tokens + elapsed * self.rate
            )
            self._last_refill = now

    # ── Dunder methods ──────────────────────────────────────────────────

    def __repr__(self) -> str:
        with self._lock:
            self._refill()
            return (
                f"TokenBucket(rate={self.rate}, capacity={self.capacity}, "
                f"burst={self.burst}, tokens={self._tokens:.2f})"
            )

    def __enter__(self) -> "TokenBucket":
        return self

    def __exit__(self, *args) -> None:
        pass
