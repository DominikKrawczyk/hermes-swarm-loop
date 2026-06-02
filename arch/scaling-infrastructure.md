# Scaling Infrastructure — 7 Scaling Modules

## Overview

The scaling layer provides 7 modules for controlling agent parallelism, rate
limiting, batch sizing, and resilience. These modules work together to keep
the swarm operating at maximum throughput without overwhelming the system.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SCALING LAYER                                  │
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │
│  │ TokenBucket  │    │  CASStore    │    │ PriorityQueue│           │
│  │ Rate control │    │ State sync   │    │ Task ordering│           │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘           │
│         │                  │                    │                    │
│         ▼                  ▼                    ▼                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │
│  │AdaptiveBatch │    │CircuitBreaker│    │ConnPool      │           │
│  │ Batch sizing │    │Fail isolation│    │ Conn reuse   │           │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘           │
│         │                  │                    │                    │
│         └──────────────────┼────────────────────┘                   │
│                            │                                        │
│                            ▼                                        │
│                    ┌──────────────┐                                 │
│                    │QueuePressure │                                 │
│                    │ Backpressure │                                 │
│                    └──────────────┘                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1. TokenBucket

**File:** `scaling/token_bucket.py`

Rate limiter using the standard token bucket algorithm.

### Configuration (from `configs/scaling.yaml`)

```yaml
token_bucket:
  default_rate: 100          # tokens per second
  default_burst: 200         # max token capacity
  per_worker_rate: 10        # tokens per individual worker
  refill_interval_ms: 100    # how often tokens are refilled
```

### State Diagram

```
   ┌─────────────┐
   │  Tokens: N  │◄──── Refill at rate/s
   └──────┬──────┘
          │ consume(n)
          ▼
   ┌─────────────┐
   │  Tokens:    │
   │  N - n      │──► n <= N → Return True
   └─────────────┘
          │ n > N
          ▼
    Return False
    (rate limited)
```

### API

```python
class TokenBucket:
    def __init__(self, rate=100.0, burst=200.0, refill_interval_ms=100.0):
        ...
    def consume(self, tokens=1.0) -> bool: ...
    def consume_or_wait(self, tokens=1.0, timeout=10.0) -> bool: ...
    @property
    def available_tokens(self) -> float: ...
    def reset(self): ...
```

---

## 2. AdaptiveBatcher

**File:** `scaling/adaptive_batcher.py`

Dynamically adjusts batch sizes based on latency feedback.

### Configuration

```yaml
adaptive_batcher:
  min_batch_size: 1
  max_batch_size: 33
  target_latency_ms: 500
  scale_up_threshold: 0.8    # Grow if latency < 80% of target
  scale_down_threshold: 0.3  # Shrink if latency > 3.33× of target
```

### Behavior

```
Latency / Target
      │
 3.33×│━━━━━━━━━━━━━ SHrink ──────────────────
      │
  1.0×│──── Target Latency ─────────────────
      │
  0.8×│━━━━━━━━━━━━━ Grow ────────────────────
      │
      └───────────────────────────────────────► Concurrency
```

### API

```python
class AdaptiveBatcher:
    def __init__(self, min_batch=1, max_batch=33,
                 target_latency_ms=500.0, ...): ...
    @property
    def current_batch_size(self) -> int: ...
    def record_latency(self, latency_ms: float, concurrency_ratio: float): ...
    def reset(self): ...
```

---

## 3. CASStore

**File:** `scaling/cas_store.py`

Compare-And-Swap state store for distributed coordination.

### Configuration

```yaml
cas_store:
  retry_on_conflict: 3
  lock_timeout_ms: 5000
  wal_mode: true
```

### API

```python
class CASStore:
    def __init__(self, db_path: str, retry_on_conflict=3,
                 lock_timeout_ms=5000, wal_mode=True): ...
    def get(self, key: str) -> dict | None: ...
    def set(self, key: str, value: Any) -> dict: ...
    def cas(self, key: str, expected: Any, new: Any) -> bool: ...
    def update(self, key: str, transform: Callable) -> bool: ...
    def delete(self, key: str) -> bool: ...
```

### CAS Update Flow

```
1. Read current:  get(key) → {value: V1, version: 1}
2. Transform:     new_value = transform(V1)
3. Write:         cas(key, V1, new_value)
                  └── UPDATE ... WHERE value = V1
                                    ┌───┐
4a. Row matched? ──► Return True  │ OK │
4b. No match?    ──► Return False └───┘
    (version changed — concurrent write)
    ┌───┐
    │   │── Retry up to retry_on_conflict times
    └───┘
```

---

## 4. CircuitBreaker

**File:** `scaling/circuit_breaker.py`

Prevents cascading failures by isolating failing components.

### Configuration

```yaml
circuit_breaker:
  failure_threshold: 5
  recovery_timeout_ms: 30000    # 30 seconds
  half_open_max_requests: 3
  consecutive_successes_to_close: 2
```

### State Machine

```
         ┌─────────────────────────┐
         │         CLOSED          │
         │   Normal operation      │
         └───────────┬─────────────┘
                     │ failures >= threshold
                     ▼
         ┌─────────────────────────┐
         │          OPEN           │
         │   Reject all requests   │
         └───────────┬─────────────┘
                     │ recovery_timeout elapsed
                     ▼
         ┌─────────────────────────┐
         │       HALF_OPEN         │
         │   Allow limited probes  │
         └───────────┬─────────────┘
                    ┌┴┐
            success │ │ failure
                    ▼ ▼
         ┌──────────┐ ┌──────────┐
         │  CLOSED  │ │   OPEN   │
         └──────────┘ └──────────┘
```

### API

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout_ms=30000.0,
                 half_open_max_requests=3,
                 consecutive_successes_to_close=2): ...
    def call(self, fn, *args, **kwargs):
        """Execute fn through the breaker. Raises CircuitBreakerOpenError if open."""
    @property
    def state(self) -> CircuitState: ...
    def reset(self): ...
```

---

## 5. ConnectionPool

**File:** `scaling/connection_pool.py`

Manages a pool of reusable connections with idle timeout and lifetime limits.

### Configuration

```yaml
connection_pool:
  min_connections: 2
  max_connections: 33
  idle_timeout_seconds: 60
  max_lifetime_seconds: 300
```

### API

```python
class ConnectionPool:
    def __init__(self, min_connections=2, max_connections=33,
                 idle_timeout_seconds=60.0, max_lifetime_seconds=300.0,
                 factory=None): ...
    def acquire(self) -> Any: ...
    def release(self, conn: Any): ...
    @property
    def available(self) -> int: ...
    @property
    def active(self) -> int: ...
    @property
    def size(self) -> int: ...
    def close_all(self): ...
```

---

## 6. PriorityQueue

**File:** `scaling/priority_queue.py`

Priority-sorted task queue with aging to prevent starvation.

### Configuration

```yaml
priority_queue:
  default_priority: 5
  max_priority: 10
  aging_factor: 0.1
  age_interval_seconds: 60
```

### Aging Mechanism

Every `age_interval_seconds`, items waiting in the queue get their effective
priority boosted by `aging_factor`. This prevents low-priority tasks from
starving indefinitely.

```
effective_priority = -(priority + age_bonus)
age_bonus = (wait_time / age_interval) * aging_factor
```

### API

```python
class PriorityQueue:
    def __init__(self, default_priority=5, max_priority=10,
                 aging_factor=0.1, age_interval_seconds=60.0): ...
    def push(self, item: Any, priority: int | None = None): ...
    def pop(self) -> Any | None: ...
    def peek(self) -> Any | None: ...
    @property
    def is_empty(self) -> bool: ...
    def __len__(self) -> int: ...
```

---

## 7. QueuePressure

**File:** `scaling/queue_pressure.py`

Monitors queue depth and applies backpressure when thresholds are exceeded.

### Configuration

```yaml
queue_pressure:
  pressure_threshold: 0.8       # 80% capacity → start throttling
  backpressure_factor: 0.5
  max_queue_depth: 1000
  auto_throttle: true
```

### Pressure Levels

```
Pressure Ratio            Level        Throttle
─────────────────────────────────────────────────
  0.00 - 0.48             NORMAL       No
  0.48 - 0.79             ELEVATED     No
  0.80 - 0.94             HIGH         Yes (linear backoff)
  0.95 - 1.00             CRITICAL     Yes (aggressive backoff)
```

### Throttle Delay

```
delay = (pressure_ratio ** 2) * backpressure_factor * 10.0
```

At 80% capacity: delay = 0.64 × 0.5 × 10 = 3.2 seconds
At 100% capacity: delay = 1.0 × 0.5 × 10 = 5.0 seconds

### API

```python
class QueuePressure:
    def __init__(self, pressure_threshold=0.8, backpressure_factor=0.5,
                 max_queue_depth=1000, auto_throttle=True): ...
    def update_depth(self, depth: int): ...
    @property
    def pressure_ratio(self) -> float: ...
    @property
    def pressure_level(self) -> PressureLevel: ...
    @property
    def should_throttle(self) -> bool: ...
    @property
    def throttle_delay(self) -> float: ...
    def reset(self): ...
```

---

## Integration Flow

```
Agent spawn request
       │
       ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  TokenBucket │───▶│ PriorityQueue│───▶│QueuePressure │
│  Rate limit  │    │  Order tasks │    │  Monitor     │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │ pressure OK?
                                               ▼
                                       ┌──────────────┐
                                       │AdaptiveBatch │
                                       │  Size batch  │
                                       └──────┬───────┘
                                              │
                                              ▼
                                       ┌──────────────┐    ┌──────────────┐
                                       │  ConnPool    │───▶│CircuitBreaker│
                                       │  Get conn    │    │  Check state │
                                       └──────────────┘    └──────────────┘
                                              │
                                              ▼
                                       Agent spawned ✅
                                       or rejected ❌
```
