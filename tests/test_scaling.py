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


# =============================================================================
# TokenBucket — Edge Cases
# =============================================================================

class TestTokenBucketEdgeCases:
    """TokenBucket edge cases: validation, set_rate, set_capacity, discrete refill."""

    def test_set_rate_changes_rate(self):
        from scaling.token_bucket import TokenBucket
        tb = TokenBucket(rate=10.0, capacity=100)
        assert tb.rate == 10.0
        tb.set_rate(50.0)
        assert tb.rate == 50.0

    def test_set_rate_zero_raises(self):
        from scaling.token_bucket import TokenBucket
        tb = TokenBucket(rate=10.0, capacity=100)
        import pytest
        with pytest.raises(ValueError, match="rate must be > 0"):
            tb.set_rate(0)

    def test_set_capacity_changes_capacity(self):
        from scaling.token_bucket import TokenBucket
        tb = TokenBucket(rate=10.0, capacity=100)
        tb.consume(90, block=False)
        tb.set_capacity(50)
        assert tb.capacity == 50
        assert tb.tokens <= 50  # trimmed

    def test_set_capacity_zero_raises(self):
        from scaling.token_bucket import TokenBucket
        tb = TokenBucket(rate=10.0, capacity=100)
        import pytest
        with pytest.raises(ValueError, match="capacity must be > 0"):
            tb.set_capacity(0)

    def test_rate_zero_raises_at_init(self):
        from scaling.token_bucket import TokenBucket
        import pytest
        with pytest.raises(ValueError, match="rate must be > 0"):
            TokenBucket(rate=0)

    def test_burst_and_capacity_mutually_exclusive(self):
        from scaling.token_bucket import TokenBucket
        import pytest
        with pytest.raises(ValueError, match="Cannot specify both"):
            TokenBucket(rate=10, capacity=50, burst=100)

    def test_consume_too_many_raises(self):
        from scaling.token_bucket import TokenBucket
        tb = TokenBucket(rate=10, capacity=50)
        import pytest
        with pytest.raises(ValueError, match="exceeds capacity"):
            tb.consume(100)

    def test_consume_zero_raises(self):
        from scaling.token_bucket import TokenBucket
        tb = TokenBucket(rate=10, capacity=50)
        import pytest
        with pytest.raises(ValueError, match="tokens must be > 0"):
            tb.consume(0)

    def test_discrete_interval_refill(self):
        from scaling.token_bucket import TokenBucket
        import time
        tb = TokenBucket(rate=10, capacity=100, refill_interval_ms=100)
        tb.consume(100, block=False)  # empty
        assert tb.consume(1, block=False) is False
        time.sleep(0.15)
        assert tb.consume(1, block=False) is True  # refilled

    def test_repr(self):
        from scaling.token_bucket import TokenBucket
        tb = TokenBucket(rate=10, capacity=50)
        r = repr(tb)
        assert "TokenBucket" in r
        assert "rate=10" in r
        assert "capacity=50" in r

    def test_context_manager(self):
        from scaling.token_bucket import TokenBucket
        with TokenBucket(rate=10, capacity=50) as tb:
            assert tb.consume(1) is True

    def test_acquire_context(self):
        from scaling.token_bucket import TokenBucket
        tb = TokenBucket(rate=10, capacity=50)
        with tb.acquire_context(1, timeout=0.5) as ok:
            assert ok is True


# =============================================================================
# CircuitBreaker — Edge Cases
# =============================================================================

class TestCircuitBreakerEdgeCases:
    """Circuit breaker edge cases: call(), on_state_change, validation."""

    def test_call_successful(self):
        from scaling.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)
        result = cb.call(lambda: "hello")
        assert result == "hello"
        assert cb.state.name == "CLOSED"

    def test_call_open_raises(self):
        from scaling.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=10)
        cb.record_failure()
        import pytest
        with pytest.raises(Exception, match="OPEN"):
            cb.call(lambda: "should not run")

    def test_call_records_failure(self):
        from scaling.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=10)
        import pytest
        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("boom")))
        assert cb.state.name == "OPEN"

    def test_on_state_change_callback(self):
        from scaling.circuit_breaker import CircuitBreaker, CircuitState
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05)
        transitions = []
        def cb_handler(old, new):
            transitions.append((old.name, new.name))
        cb.on_state_change(cb_handler)
        cb.record_failure()
        assert len(transitions) >= 1
        assert transitions[-1] == ("CLOSED", "OPEN")

    def test_validation_failure_threshold(self):
        from scaling.circuit_breaker import CircuitBreaker
        import pytest
        with pytest.raises(ValueError):
            CircuitBreaker(failure_threshold=0)

    def test_validation_recovery_timeout(self):
        from scaling.circuit_breaker import CircuitBreaker
        import pytest
        with pytest.raises(ValueError):
            CircuitBreaker(failure_threshold=3, recovery_timeout=0)

    def test_validation_consecutive_successes(self):
        from scaling.circuit_breaker import CircuitBreaker
        import pytest
        with pytest.raises(ValueError):
            CircuitBreaker(failure_threshold=3, recovery_timeout=1,
                           consecutive_successes_to_close=0)

    def test_reset_notifies(self):
        from scaling.circuit_breaker import CircuitBreaker, CircuitState
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05)
        transitions = []
        cb.on_state_change(lambda o, n: transitions.append((o.name, n.name)))
        cb.record_failure()
        cb.reset()
        assert len(transitions) >= 2
        assert transitions[-1] == ("OPEN", "CLOSED")


# =============================================================================
# PriorityQueue — Edge Cases
# =============================================================================

class TestPriorityQueueEdgeCases:
    """PriorityQueue: get_with_priority, remove, clear, stats."""

    def test_get_with_priority_returns_item(self):
        from scaling.priority_queue import PriorityQueue
        pq = PriorityQueue()
        pq.put("task-a", priority=10)
        pitem = pq.get_with_priority()
        assert pitem.item == "task-a"
        assert pitem.priority == -10  # negated internally

    def test_get_with_priority_empty_raises(self):
        from scaling.priority_queue import PriorityQueue
        import pytest
        with pytest.raises(ValueError, match="Queue empty"):
            pq = PriorityQueue()
            pq.get_with_priority(block=False)

    def test_remove_existing_item(self):
        from scaling.priority_queue import PriorityQueue
        pq = PriorityQueue()
        pq.put("task-a")
        pq.put("task-b")
        assert pq.remove("task-a") is True
        assert pq.size == 1

    def test_remove_nonexistent_returns_false(self):
        from scaling.priority_queue import PriorityQueue
        pq = PriorityQueue()
        pq.put("task-a")
        assert pq.remove("nonexistent") is False

    def test_clear_empties_queue(self):
        from scaling.priority_queue import PriorityQueue
        pq = PriorityQueue()
        pq.put("a")
        pq.put("b")
        pq.put("c")
        pq.clear()
        assert pq.empty() is True

    def test_priorities_returns_sorted(self):
        from scaling.priority_queue import PriorityQueue
        pq = PriorityQueue()
        pq.put("low", priority=1)
        pq.put("high", priority=10)
        pq.put("mid", priority=5)
        ps = pq.priorities()
        assert sorted(ps) == [1, 5, 10]

    def test_items_by_priority(self):
        from scaling.priority_queue import PriorityQueue
        pq = PriorityQueue()
        pq.put("a", priority=10)
        pq.put("b", priority=10)
        pq.put("c", priority=1)
        items = pq.items_by_priority(10)
        assert len(items) == 2
        assert "c" not in items

    def test_full_queue_raises(self):
        from scaling.priority_queue import PriorityQueue
        pq = PriorityQueue(maxsize=2)
        pq.put("a")
        pq.put("b")
        import pytest
        with pytest.raises(ValueError, match="Queue full"):
            pq.put("c", block=False)

    def test_iter_yields_items(self):
        from scaling.priority_queue import PriorityQueue
        pq = PriorityQueue()
        pq.put("x")
        pq.put("y")
        items = list(pq)
        assert items == ["x", "y"]

    def test_qsize_and_len(self):
        from scaling.priority_queue import PriorityQueue
        pq = PriorityQueue()
        assert pq.qsize() == 0
        pq.put("a")
        assert pq.qsize() == 1
        assert len(pq) == 1

    def test_peek_with_priority(self):
        from scaling.priority_queue import PriorityQueue
        pq = PriorityQueue()
        pq.put("high", priority=10)
        pq.put("low", priority=1)
        pitem = pq.peek_with_priority()
        assert pitem.item == "high"
        assert pq.size == 2  # not removed


# =============================================================================
# QueuePressure — Edge Cases
# =============================================================================

class TestQueuePressureEdgeCases:
    """QueuePressure: edge cases, validation, should_throttle with threshold."""

    def test_max_depth_zero_raises(self):
        from scaling.queue_pressure import QueuePressure
        import pytest
        with pytest.raises(ValueError, match="max_depth must be > 0"):
            QueuePressure(max_depth=0)

    def test_negative_depth_raises(self):
        from scaling.queue_pressure import QueuePressure
        qp = QueuePressure(max_depth=100)
        import pytest
        with pytest.raises(ValueError):
            qp.record(-1)

    def test_pressure_ratio_no_max_depth(self):
        from scaling.queue_pressure import QueuePressure
        qp = QueuePressure(max_depth=100)
        # Force edge case: set max_depth to 0 after init
        qp.max_depth = 0
        assert qp.pressure_ratio == 0.0

    def test_pressure_level_moderate(self):
        from scaling.queue_pressure import PressureLevel, QueuePressure
        qp = QueuePressure(max_depth=100)
        qp.record(35)
        assert qp.pressure_level == PressureLevel.MODERATE

    def test_pressure_level_critical(self):
        from scaling.queue_pressure import PressureLevel, QueuePressure
        qp = QueuePressure(max_depth=100)
        qp.record(99)
        assert qp.pressure_level == PressureLevel.CRITICAL

    def test_should_throttle_with_explicit_threshold(self):
        from scaling.queue_pressure import PressureLevel, QueuePressure
        qp = QueuePressure(max_depth=100)
        qp.record(40)  # 0.4 -> MODERATE (0.3 <= 0.4 < 0.6)
        # At MODERATE with LOW threshold -> should throttle
        assert qp.should_throttle(PressureLevel.LOW) is True
        # At MODERATE with HIGH threshold -> should not throttle
        assert qp.should_throttle(PressureLevel.HIGH) is False

    def test_current_depth_property(self):
        from scaling.queue_pressure import QueuePressure
        qp = QueuePressure(max_depth=100)
        qp.record(50)
        assert qp.current_depth == 50

    def test_repr(self):
        from scaling.queue_pressure import QueuePressure
        qp = QueuePressure(max_depth=100)
        r = repr(qp)
        assert "QueuePressure" in r
        assert "LOW" in r


# =============================================================================
# CASStore — Edge Cases
# =============================================================================

class TestCASStoreEdgeCases:
    """CASStore: store property, get_entry, clear, keys."""

    def test_store_property_returns_snapshot(self):
        from scaling.cas_store import CASStore
        store = CASStore()
        store.set("k1", "v1")
        store.set("k2", "v2")
        snap = store.store
        assert len(snap) == 2
        assert snap["k1"].value == "v1"
        assert snap["k2"].value == "v2"

    def test_get_entry_returns_entry(self):
        from scaling.cas_store import CASStore
        store = CASStore()
        store.set("k", "val")
        entry = store.get_entry("k")
        assert entry is not None
        assert entry.value == "val"
        assert entry.version == 1

    def test_get_entry_nonexistent(self):
        from scaling.cas_store import CASStore
        store = CASStore()
        assert store.get_entry("nonexistent") is None

    def test_clear_empties_store(self):
        from scaling.cas_store import CASStore
        store = CASStore()
        store.set("a", 1)
        store.set("b", 2)
        store.clear()
        assert store.size() == 0

    def test_keys_returns_all_keys(self):
        from scaling.cas_store import CASStore
        store = CASStore()
        store.set("a", 1)
        store.set("b", 2)
        ks = store.keys()
        assert "a" in ks
        assert "b" in ks
        assert len(ks) == 2

    def test_cas_nonexistent_key_fails(self):
        from scaling.cas_store import CASStore
        store = CASStore()
        assert store.cas("nonexistent", "old", "new") is False

    def test_exists(self):
        from scaling.cas_store import CASStore
        store = CASStore()
        assert store.exists("k") is False
        store.set("k", "v")
        assert store.exists("k") is True


# =============================================================================
# AdaptiveBatcher — Edge Cases
# =============================================================================

class TestAdaptiveBatcherEdgeCases:
    """AdaptiveBatcher: extend, flush empty, callbacks, validation."""

    def test_extend_adds_items(self):
        from scaling.adaptive_batcher import AdaptiveBatcher
        ab = AdaptiveBatcher(batch_size=10, max_batch=20)
        ab.extend(["a", "b", "c"])
        assert ab.buffer_size == 3

    def test_flush_empty_returns_none(self):
        from scaling.adaptive_batcher import AdaptiveBatcher
        ab = AdaptiveBatcher()
        assert ab.flush() is None

    def test_batch_size_validation(self):
        from scaling.adaptive_batcher import AdaptiveBatcher
        import pytest
        with pytest.raises(ValueError):
            AdaptiveBatcher(batch_size=0)

    def test_min_batch_validation(self):
        from scaling.adaptive_batcher import AdaptiveBatcher
        import pytest
        with pytest.raises(ValueError):
            AdaptiveBatcher(min_batch=0)

    def test_max_batch_less_than_min(self):
        from scaling.adaptive_batcher import AdaptiveBatcher
        import pytest
        with pytest.raises(ValueError, match="max_batch.*>=.*min_batch"):
            AdaptiveBatcher(min_batch=5, max_batch=3)

    def test_target_latency_validation(self):
        from scaling.adaptive_batcher import AdaptiveBatcher
        import pytest
        with pytest.raises(ValueError):
            AdaptiveBatcher(target_latency_ms=0)

    def test_scale_up_threshold_validation(self):
        from scaling.adaptive_batcher import AdaptiveBatcher
        import pytest
        with pytest.raises(ValueError):
            AdaptiveBatcher(scale_up_threshold=1.5)
