"""
Circuit Breaker state machine.

Implements a configurable circuit breaker pattern with CLOSED -> OPEN -> HALF_OPEN
state transitions, configurable failure threshold, recovery timeout, and
consecutive-success-based recovery.
"""

import threading
import time
from collections.abc import Callable
from enum import Enum, auto
from typing import TypeVar

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = auto()
    OPEN = auto()
    HALF_OPEN = auto()


class CircuitBreakerOpenError(Exception):
    """Raised when a request is attempted while the circuit is OPEN."""


class CircuitBreaker:
    """Configurable circuit breaker state machine.

    Parameters
    ----------
    failure_threshold : int
        Number of consecutive failures before the circuit opens.
    recovery_timeout : float
        Seconds to wait in OPEN state before transitioning to HALF_OPEN.
    consecutive_successes_to_close : int, optional
        Number of consecutive successes in HALF_OPEN needed to transition back
        to CLOSED (default 1).
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        consecutive_successes_to_close: int = 1,
    ) -> None:
        if failure_threshold <= 0:
            raise ValueError(
                f"failure_threshold must be > 0, got {failure_threshold}"
            )
        if recovery_timeout <= 0:
            raise ValueError(
                f"recovery_timeout must be > 0, got {recovery_timeout}"
            )
        if consecutive_successes_to_close <= 0:
            raise ValueError(
                f"consecutive_successes_to_close must be > 0, "
                f"got {consecutive_successes_to_close}"
            )

        self.failure_threshold: int = failure_threshold
        self.recovery_timeout: float = recovery_timeout
        self.consecutive_successes_to_close: int = consecutive_successes_to_close

        self._state: CircuitState = CircuitState.CLOSED
        self._consecutive_failures: int = 0
        self._consecutive_successes: int = 0
        self._last_failure_time: float = 0.0
        self._lock = threading.RLock()
        self._on_state_change: Callable[[CircuitState, CircuitState], None] | None = None
        self._half_open_max_probes: int = 1
        self._half_open_in_flight: int = 0

    # -- State property ---------------------------------------------------------

    @property
    def state(self) -> CircuitState:
        """Current circuit breaker state (auto-transitions on read if timeout elapsed)."""
        with self._lock:
            self._check_timeout()
            return self._state

    # -- Convenience properties -------------------------------------------------

    @property
    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    @property
    def is_closed(self) -> bool:
        return self.state == CircuitState.CLOSED

    @property
    def is_half_open(self) -> bool:
        return self.state == CircuitState.HALF_OPEN

    # -- Public API -------------------------------------------------------------

    def allows_request(self) -> bool:
        """Return True if the circuit accepts requests (CLOSED or HALF_OPEN with capacity)."""
        with self._lock:
            self._check_timeout()
            if self._state == CircuitState.CLOSED:
                return True
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_in_flight < self._half_open_max_probes:
                    self._half_open_in_flight += 1
                    return True
            return False

    def record_success(self) -> None:
        """Record a successful call.

        In HALF_OPEN state, increments the consecutive success counter.
        Transitions to CLOSED when consecutive_successes_to_close is reached.
        If the circuit is OPEN but recovery timeout has elapsed,
        transitions to HALF_OPEN first.
        """
        with self._lock:
            self._check_timeout()
            if self._state == CircuitState.OPEN:
                return
            self._consecutive_failures = 0

            if self._state == CircuitState.HALF_OPEN:
                self._half_open_in_flight = max(0, self._half_open_in_flight - 1)
                self._consecutive_successes += 1
                if self._consecutive_successes >= self.consecutive_successes_to_close:
                    self._transition(CircuitState.CLOSED)
            else:
                self._consecutive_successes = 0

    def record_failure(self) -> None:
        """Record a failed call.

        In CLOSED state, increments the failure counter and opens the circuit
        when the threshold is reached. In HALF_OPEN state, immediately re-opens.
        Decrements the HALF_OPEN in-flight counter if applicable.
        """
        with self._lock:
            self._consecutive_failures += 1
            self._consecutive_successes = 0
            self._last_failure_time = time.monotonic()

            if self._state == CircuitState.HALF_OPEN:
                self._half_open_in_flight = max(0, self._half_open_in_flight - 1)
                self._transition(CircuitState.OPEN)
            elif (
                self._state == CircuitState.CLOSED
                and self._consecutive_failures >= self.failure_threshold
            ):
                self._transition(CircuitState.OPEN)

    def reset(self) -> None:
        """Reset the circuit breaker to CLOSED state with clean counters."""
        with self._lock:
            old = self._state
            self._state = CircuitState.CLOSED
            self._consecutive_failures = 0
            self._consecutive_successes = 0
            self._half_open_in_flight = 0
            self._last_failure_time = 0.0
            if old != CircuitState.CLOSED:
                self._notify_state_change(old, CircuitState.CLOSED)

    def call(self, fn: Callable[..., T], *args, **kwargs) -> T:
        """Execute *fn*, automatically recording success or failure.

        Raises CircuitBreakerOpenError if the circuit is OPEN.

        Returns the return value of *fn* on success.
        """
        if not self.allows_request():
            raise CircuitBreakerOpenError("Circuit is OPEN")
        try:
            result = fn(*args, **kwargs)
        except Exception:
            self.record_failure()
            raise
        else:
            self.record_success()
            return result

    def on_state_change(
        self, cb: Callable[[CircuitState, CircuitState], None]
    ) -> None:
        """Register a callback invoked on state transitions: ``cb(old, new)``."""
        self._on_state_change = cb

    # -- Internal helpers -------------------------------------------------------

    def _check_timeout(self) -> None:
        """Transition from OPEN to HALF_OPEN if recovery timeout has elapsed."""
        if self._state != CircuitState.OPEN:
            return
        elapsed = time.monotonic() - self._last_failure_time
        if elapsed >= self.recovery_timeout:
            self._transition(CircuitState.HALF_OPEN)

    def _transition(self, new_state: CircuitState) -> None:
        if self._state == new_state:
            return
        old = self._state
        self._state = new_state
        if new_state == CircuitState.HALF_OPEN:
            self._consecutive_successes = 0
            self._half_open_in_flight = 0
        if new_state == CircuitState.CLOSED:
            self._half_open_in_flight = 0
        self._notify_state_change(old, new_state)

    def _notify_state_change(
        self, old: CircuitState, new: CircuitState
    ) -> None:
        if self._on_state_change is not None:
            try:
                self._on_state_change(old, new)
            except Exception:
                pass

    def __repr__(self) -> str:
        with self._lock:
            return (
                f"CircuitBreaker(state={self._state.name}, "
                f"failures={self._consecutive_failures}, "
                f"threshold={self.failure_threshold})"
            )
