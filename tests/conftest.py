"""pytest fixtures for Hermes Swarm Loop tests.

Provides StateDB, PhaseMachine, PointMachine, YOLOMachine, MasteryGate
fixtures backed by a tmp_path SQLite database, plus scaling module fixtures.
"""

import pytest
from pathlib import Path


# ── Engine Fixtures ───────────────────────────────────────────────

@pytest.fixture
def db_path(tmp_path: Path) -> str:
    """Temporary SQLite database path."""
    return str(tmp_path / "test_swarm.db")


@pytest.fixture
def statedb(db_path: str):
    """StateDB fixture — opens a fresh SQLite DB with WAL mode and all tables."""
    from engine.state_machine import StateDB
    db = StateDB(db_path)
    db.open()
    db.ensure_schema()
    yield db
    db.close()


@pytest.fixture
def phase_machine(statedb):
    """PhaseMachine backed by a fresh StateDB."""
    from engine.state_machine import PhaseMachine
    return PhaseMachine(statedb)


@pytest.fixture
def point_machine(statedb):
    """PointMachine backed by a fresh StateDB."""
    from engine.state_machine import PointMachine
    return PointMachine(statedb)


@pytest.fixture
def yolo_machine(statedb):
    """YOLOMachine backed by a fresh StateDB."""
    from engine.state_machine import YOLOMachine
    return YOLOMachine(statedb)


@pytest.fixture
def mastery_gate():
    """MasteryGate with default 7-dim weights."""
    from engine.mastery_gate import MasteryGate
    return MasteryGate()


@pytest.fixture
def score_all_high():
    """ScoreCard with all 7 dims at PASS threshold (>= 0.70)."""
    from engine.mastery_gate import ScoreCard
    s = ScoreCard()
    s.correctness = 0.95
    s.safety = 0.92
    s.test_coverage = 0.90
    s.consistency = 0.93
    s.diversity = 0.88
    s.efficiency = 0.85
    s.clarity = 0.90
    return s


@pytest.fixture
def score_medium():
    """ScoreCard at CROSS-CHECK level (0.50–0.69)."""
    from engine.mastery_gate import ScoreCard
    s = ScoreCard()
    s.correctness = 0.60
    s.safety = 0.55
    s.test_coverage = 0.50
    s.consistency = 0.58
    s.diversity = 0.52
    s.efficiency = 0.55
    s.clarity = 0.65
    return s


@pytest.fixture
def score_low():
    """ScoreCard at BLOCK level (< 0.30)."""
    from engine.mastery_gate import ScoreCard
    s = ScoreCard()
    s.correctness = 0.20
    s.safety = 0.15
    s.test_coverage = 0.10
    s.consistency = 0.25
    s.diversity = 0.20
    s.efficiency = 0.15
    s.clarity = 0.30
    return s


@pytest.fixture
def score_perfect():
    """ScoreCard at perfect 1.0 across all dims."""
    from engine.mastery_gate import ScoreCard
    s = ScoreCard()
    for dim in ["correctness", "safety", "test_coverage", "consistency",
                "diversity", "efficiency", "clarity"]:
        setattr(s, dim, 1.0)
    return s


# ── Scaling Fixtures ──────────────────────────────────────────────

@pytest.fixture
def token_bucket():
    """TokenBucket(rate=100, capacity=200)."""
    from scaling.token_bucket import TokenBucket
    return TokenBucket(rate=100.0, capacity=200.0)


@pytest.fixture
def circuit_breaker():
    """CircuitBreaker(failure_threshold=3, recovery_timeout=0.1s)."""
    from scaling.circuit_breaker import CircuitBreaker
    return CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)


@pytest.fixture
def connection_pool():
    """ConnectionPool with factory and max_size=5."""
    from scaling.connection_pool import ConnectionPool
    return ConnectionPool(factory=lambda: "conn", max_size=5, acquire_timeout=10.0,
                          validate=lambda c: True, close_fn=lambda c: None)


@pytest.fixture
def priority_queue():
    """PriorityQueue with default_priority=0."""
    from scaling.priority_queue import PriorityQueue
    return PriorityQueue(maxsize=0, default_priority=0)


@pytest.fixture
def cas_store():
    """CASStore."""
    from scaling.cas_store import CASStore
    return CASStore()


@pytest.fixture
def queue_pressure():
    """QueuePressure with max_depth=100."""
    from scaling.queue_pressure import QueuePressure
    return QueuePressure(max_depth=100)
