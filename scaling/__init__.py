"""
Scaling Modules for Hermes Swarm Loop
======================================
"""
from __future__ import annotations

from .adaptive_batcher import AdaptiveBatcher, Batch
from .cas_store import CASStore
from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState
from .connection_pool import (
    ConnectionClosedError,
    ConnectionPool,
    ConnectionTimeoutError,
    PooledConnection,
    PoolStats,
)
from .priority_queue import PriorityItem, PriorityQueue, PriorityQueueStats, QueueEmpty, QueueFull
from .queue_pressure import PressureLevel, PressureMetrics, QueuePressure, Sample
from .token_bucket import TokenBucket

__all__ = ["AdaptiveBatcher", "Batch", "CASStore", "CircuitBreaker", "CircuitBreakerOpenError", "CircuitState", "ConnectionClosedError", "ConnectionPool", "ConnectionTimeoutError", "PoolStats", "PooledConnection", "PressureLevel", "PressureMetrics", "PriorityItem", "PriorityQueue", "PriorityQueueStats", "QueueEmpty", "QueueFull", "QueuePressure", "Sample", "TokenBucket"]
__version__ = "0.1.0"
