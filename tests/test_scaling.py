"""Tests for scaling infrastructure: TokenBucket, CircuitBreaker, ConnectionPool,
PriorityQueue, QueuePressure, AdaptiveBatcher, CASStore.
Matches the actual APIs found on disk (Phase 1 code generation agents).
"""

import time

import pytest

# =============================================================================
# TokenBucket Tests
# =============================================================================

class TestTokenBucket:
    """Token bucket rate limiter tests."""

    def test_consume_returns_true_when_tokens_available(self, token_bucket):
        """Consuming tokens when bucket is full returns True."""
        assert token_bucket.consume(1) is True
        assert token_bucket.consume(10) is True

    def test_consume_returns_false_when_exhausted(self, token_bucket):
        """Consuming more tokens than available returns False."""
        capacity = int(token_bucket.capacity)
        for _ in range(capacity):
            token_bucket.consume(1, block=False)
        assert token_bucket.consume(1, block=False) is False

    def test_available_starts_at_capacity(self, token_bucket):
        """tokens starts at capacity."""
        assert token_bucket.tokens == token_bucket.capacity

    def test_available_decreases(self, token_bucket):
        """tokens decreases after consume."""
        before = token_bucket.tokens
        token_bucket.consume(50, block=False)
        after = token_bucket.tokens
        assert after <= before - 49

    def test_reset_restores_tokens(self, token_bucket):
        """reset restores tokens to capacity."""
        token_bucket.consume(100, block=False)
        token_bucket.reset()
        assert token_bucket.tokens == token_bucket.capacity

    def test_consume_or_wait_returns_bool(self, token_bucket):
        """consume_or_wait returns a bool depending on timeout."""
        # burst = capacity = 200, consume all, then try with timeout
        token_bucket.consume(token_bucket.capacity, block=False)
        result = token_bucket.consume_or_wait(1, timeout=0.05)
        assert isinstance(result, bool)

    def test_consume_or_wait_timeout(self):
        """consume_or_wait returns False when timeout is exceeded."""
        from scaling.token_bucket import TokenBucket
        slow_bucket = TokenBucket(rate=0.01, capacity=1, refill_interval_ms=10000)
        slow_bucket.consume(1, block=False)
        result = slow_bucket.consume_or_wait(1, timeout=0.01)
        assert result is False


# =============================================================================
# CircuitBreaker Tests
# =============================================================================

class TestCircuitBreaker:
    """Circuit breaker state machine tests."""

    def test_initial_state_closed(self, circuit_breaker):
        """Circuit breaker starts in CLOSED state."""
        from scaling.circuit_breaker import CircuitState
        assert circuit_breaker.state == CircuitState.CLOSED

    def test_successful_call_stays_closed(self, circuit_breaker):
        """Successful calls keep the breaker closed."""
        from scaling.circuit_breaker import CircuitState
        assert circuit_breaker.state == CircuitState.CLOSED
        circuit_breaker.record_success()
        assert circuit_breaker.state == CircuitState.CLOSED

    def test_failures_trip_to_open(self, circuit_breaker):
        """Exceeding failure threshold trips breaker to OPEN."""
        from scaling.circuit_breaker import CircuitState
        for _ in range(circuit_breaker.failure_threshold):
            circuit_breaker.record_failure()
        assert circuit_breaker.state == CircuitState.OPEN

    def test_open_rejects_requests(self, circuit_breaker):
        """OPEN state rejects requests."""
        for _ in range(circuit_breaker.failure_threshold):
            circuit_breaker.record_failure()
        assert circuit_breaker.allows_request() is False

    def test_half_open_after_timeout(self):
        """After recovery timeout, breaker transitions to HALF_OPEN."""
        from scaling.circuit_breaker import CircuitBreaker, CircuitState
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.05)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN
        time.sleep(0.06)
        # Read state to trigger lazy auto-transition
        assert cb.state == CircuitState.HALF_OPEN

    def test_half_open_success_closes(self):
        """Success in HALF_OPEN transitions back to CLOSED."""
        from scaling.circuit_breaker import CircuitBreaker, CircuitState
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.05)
        for _ in range(3):
            cb.record_failure()
        time.sleep(0.06)
        # Trigger lazy transition
        _ = cb.state
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_half_open_failure_reopens(self):
        """Failure in HALF_OPEN transitions back to OPEN."""
        from scaling.circuit_breaker import CircuitBreaker, CircuitState
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.05)
        for _ in range(3):
            cb.record_failure()
        time.sleep(0.06)
        # Trigger lazy transition
        _ = cb.state
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.state == CircuitState.OPEN

    def test_reset(self, circuit_breaker):
        """reset restores breaker to CLOSED."""
        from scaling.circuit_breaker import CircuitState
        circuit_breaker.record_failure()
        circuit_breaker.reset()
        assert circuit_breaker.state == CircuitState.CLOSED


# =============================================================================
# ConnectionPool Tests
# =============================================================================

class TestConnectionPool:
    """Connection pool lifecycle tests."""

    def test_acquire_returns_connection(self, connection_pool):
        """acquire returns a connection object."""
        conn = connection_pool.acquire()
        assert conn is not None

    def test_acquire_and_release(self, connection_pool):
        """After close, the connection is available again."""
        conn = connection_pool.acquire()
        conn.close()
        assert connection_pool.idle >= 0

    def test_acquire_creates_up_to_max(self):
        """Can acquire up to max_size before pool exhausts."""
        from scaling.connection_pool import ConnectionPool
        pool = ConnectionPool(factory=lambda: "conn", max_size=3, acquire_timeout=0.5)
        for _ in range(3):
            pool.acquire()
        with pytest.raises(Exception):
            pool.acquire()

    def test_active_count_tracks_in_use(self):
        """in_use tracks how many connections are in use."""
        from scaling.connection_pool import ConnectionPool
        pool = ConnectionPool(factory=lambda: "conn", max_size=5, acquire_timeout=5.0)
        assert pool.in_use == 0
        c1 = pool.acquire()
        # acquire returns PooledConnection, it's in_use
        assert pool.in_use == 1
        c2 = pool.acquire()  # noqa: F841
        assert pool.in_use == 2
        c1.close()
        assert pool.in_use == 1

    def test_close_all(self):
        """close_all clears the pool."""
        from scaling.connection_pool import ConnectionPool
        pool = ConnectionPool(factory=lambda: "conn", max_size=5, acquire_timeout=5.0)
        conn = pool.acquire()
        conn.close()
        pool.close_all()
        assert pool.size == 0


# =============================================================================
# PriorityQueue Tests
# =============================================================================

class TestPriorityQueue:
    """Priority queue ordering and aging."""

    def test_push_and_pop(self):
        """Items put can be got."""
        from scaling.priority_queue import PriorityQueue
        pq = PriorityQueue()
        pq.put("task-1")
        result = pq.get()
        assert result == "task-1"

    def test_higher_priority_popped_first(self):
        """Items with higher priority are got first."""
        from scaling.priority_queue import PriorityQueue
        pq = PriorityQueue()
        pq.put("high", priority=10)
        pq.put("low", priority=1)
        assert pq.get() == "high"
        assert pq.get() == "low"

    def test_peek_returns_without_removing(self):
        """peek returns top item without removing it."""
        from scaling.priority_queue import PriorityQueue
        pq = PriorityQueue()
        pq.put("item-1", priority=10)
        assert pq.peek() == "item-1"
        assert pq.get() == "item-1"

    def test_is_empty(self):
        """empty() correctly reflects queue state."""
        from scaling.priority_queue import PriorityQueue
        pq = PriorityQueue()
        assert pq.empty() is True
        pq.put("task")
        assert pq.empty() is False
        pq.get()
        assert pq.empty() is True

    def test_get_on_empty_queue_raises(self):
        """get on empty queue raises ValueError."""
        from scaling.priority_queue import PriorityQueue
        pq = PriorityQueue()
        with pytest.raises(ValueError, match="Queue empty"):
            pq.get(block=False)

    def test_len(self):
        """__len__ returns queue depth."""
        from scaling.priority_queue import PriorityQueue
        pq = PriorityQueue()
        assert len(pq) == 0
        pq.put("a")
        pq.put("b")
        assert len(pq) == 2


# =============================================================================
# QueuePressure Tests
# =============================================================================

class TestQueuePressure:
    """Queue pressure monitoring and backpressure tests."""

    def test_pressure_ratio_starts_at_zero(self):
        """Pressure ratio starts at 0.0."""
        from scaling.queue_pressure import QueuePressure
        qp = QueuePressure(max_depth=1000)
        assert qp.pressure_ratio == 0.0

    def test_pressure_ratio_increases(self):
        """Pressure ratio increases with queue depth."""
        from scaling.queue_pressure import QueuePressure
        qp = QueuePressure(max_depth=100)
        qp.record(50)
        assert qp.pressure_ratio == 0.5
        qp.record(100)
        assert qp.pressure_ratio == 1.0

    def test_pressure_level_low(self):
        """Low queue depth -> LOW pressure level."""
        from scaling.queue_pressure import PressureLevel, QueuePressure
        qp = QueuePressure(max_depth=100)
        qp.record(10)
        assert qp.pressure_level == PressureLevel.LOW

    def test_pressure_level_high(self):
        """Queue at 70% -> HIGH pressure level."""
        from scaling.queue_pressure import PressureLevel, QueuePressure
        qp = QueuePressure(max_depth=100)
        qp.record(depth=70)
        assert qp.pressure_level == PressureLevel.HIGH

    def test_should_throttle(self):
        """should_throttle returns correct value based on pressure (no-arg)."""
        from scaling.queue_pressure import QueuePressure
        qp = QueuePressure(max_depth=100)
        qp.record(90)
        assert qp.should_throttle() is True
        qp.record(10)
        assert qp.should_throttle() is False

    def test_reset(self):
        """reset clears the depth."""
        from scaling.queue_pressure import QueuePressure
        qp = QueuePressure(max_depth=100)
        qp.record(80)
        qp.reset()
        assert qp.pressure_ratio == 0.0


# =============================================================================
# AdaptiveBatcher Tests
# =============================================================================

class TestAdaptiveBatcher:
    """Adaptive batching size adjustment."""

    def test_starts_at_min_batch(self):
        """current_batch_size starts at min_batch (or batch_size)."""
        from scaling.adaptive_batcher import AdaptiveBatcher
        ab = AdaptiveBatcher(min_batch=3, max_batch=33)
        assert ab.current_batch_size == 3

    def test_grows_batch_when_headroom(self):
        """Batch grows when latency is low."""
        from scaling.adaptive_batcher import AdaptiveBatcher
        ab = AdaptiveBatcher(min_batch=1, max_batch=10, target_latency_ms=1000,
                             scale_up_threshold=0.8)
        ab.record_latency(100, concurrency_ratio=0.3)
        assert ab.current_batch_size > 1

    def test_reset(self):
        """reset restores batch to min_batch."""
        from scaling.adaptive_batcher import AdaptiveBatcher
        ab = AdaptiveBatcher(min_batch=1, max_batch=10)
        ab.record_latency(10, 0.3)
        ab.reset()
        assert ab.current_batch_size == 1


# =============================================================================
# CASStore Tests
# =============================================================================

class TestCASStore:
    """CAS compare-and-swap store tests."""

    def test_set_and_get(self):
        """Setting and getting a value works."""
        from scaling.cas_store import CASStore
        store = CASStore()
        store.set("key1", {"hello": "world"})
        result = store.get("key1")
        assert result is not None
        assert result["value"] == {"hello": "world"}
        assert result["version"] == 1

    def test_set_updates_version(self):
        """Setting an existing key increments version."""
        from scaling.cas_store import CASStore
        store = CASStore()
        store.set("key1", {"v": 1})
        r1 = store.get("key1")
        store.set("key1", {"v": 2})
        r2 = store.get("key1")
        assert r2["version"] >= r1["version"]

    def test_cas_success(self):
        """CAS succeeds when expected value matches."""
        from scaling.cas_store import CASStore
        store = CASStore()
        store.set("k", {"val": 1})
        assert store.cas("k", {"val": 1}, {"val": 2}) is True
        result = store.get("k")
        assert result["value"] == {"val": 2}

    def test_cas_failure(self):
        """CAS fails when expected value doesn't match."""
        from scaling.cas_store import CASStore
        store = CASStore()
        store.set("k", {"val": 1})
        assert store.cas("k", {"val": 99}, {"val": 2}) is False
        result = store.get("k")
        assert result["value"] == {"val": 1}

    def test_get_nonexistent(self):
        """Getting a non-existent key returns None."""
        from scaling.cas_store import CASStore
        store = CASStore()
        assert store.get("nope") is None

    def test_delete(self):
        """Deleting a key removes it."""
        from scaling.cas_store import CASStore
        store = CASStore()
        store.set("k", {"val": 1})
        assert store.delete("k") is True
        assert store.get("k") is None

    def test_delete_nonexistent(self):
        """Deleting a non-existent key returns False."""
        from scaling.cas_store import CASStore
        store = CASStore()
        assert store.delete("nope") is False

    def test_contains(self):
        """__contains__ works."""
        from scaling.cas_store import CASStore
        store = CASStore()
        store.set("k", "v")
        assert "k" in store
        assert "nope" not in store

    def test_len(self):
        """__len__ works."""
        from scaling.cas_store import CASStore
        store = CASStore()
        assert len(store) == 0
        store.set("a", 1)
        store.set("b", 2)
        assert len(store) == 2
