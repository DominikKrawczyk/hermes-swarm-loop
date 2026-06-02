"""
State Machine Engine — Hermes Swarm Loop
========================================
Three machines sharing one SQLite DB with WAL mode + optimistic CAS.

Machines:
  PhaseMachine  — tracks which phase is active and its overall status
  PointMachine  — tracks individual point status (todo/running/done/blocked)
  YOLOMachine   — governs auto-approve behaviour and parallel caps

All transitions are idempotent and emit audit events.
"""

import json
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# ─── Dataclasses ─────────────────────────────────────────────────

@dataclass
class PhaseEntry:
    id: int = 0
    phase: str = ""
    status: str = "todo"
    started_at: str | None = None
    completed_at: str | None = None
    total_points: int = 0
    completed_points: int = 0
    version: int = 1

@dataclass
class PointEntry:
    id: int = 0
    phase: str = ""
    point: str = ""
    status: str = "todo"
    agent_count: int = 0
    started_at: str | None = None
    completed_at: str | None = None
    version: int = 1

@dataclass
class YOLOState:
    id: int = 1
    zone: str = "safe"
    auto_approve: bool = False
    max_parallel: int = 5
    safety_valve_active: bool = False
    consecutive_errors: int = 0
    version: int = 1

    def __post_init__(self):
        # SQLite returns INTEGER (0/1) for bool columns — convert for `is True`/`is False` checks
        if isinstance(self.auto_approve, int):
            self.auto_approve = bool(self.auto_approve)
        if isinstance(self.safety_valve_active, int):
            self.safety_valve_active = bool(self.safety_valve_active)


class ConflictError(Exception):
    """Raised when optimistic CAS detects a version mismatch."""
    pass


# ─── DB Layer ────────────────────────────────────────────────────

class StateDB:
    """SQLite-backed state store with WAL mode and thread-safe writes."""

    _SCHEMA = """
    CREATE TABLE IF NOT EXISTS phase_state (
        id INTEGER PRIMARY KEY,
        phase TEXT NOT NULL UNIQUE,
        status TEXT NOT NULL DEFAULT 'todo',
        started_at TEXT,
        completed_at TEXT,
        total_points INTEGER DEFAULT 0,
        completed_points INTEGER DEFAULT 0,
        version INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS point_state (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phase TEXT NOT NULL,
        point TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'todo',
        agent_count INTEGER DEFAULT 0,
        started_at TEXT,
        completed_at TEXT,
        version INTEGER DEFAULT 1,
        UNIQUE(phase, point)
    );
    CREATE TABLE IF NOT EXISTS yolo_state (
        id INTEGER PRIMARY KEY,
        zone TEXT NOT NULL DEFAULT 'safe',
        auto_approve INTEGER NOT NULL DEFAULT 0,
        max_parallel INTEGER NOT NULL DEFAULT 5,
        safety_valve_active INTEGER NOT NULL DEFAULT 0,
        consecutive_errors INTEGER NOT NULL DEFAULT 0,
        version INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS event_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT NOT NULL,
        payload TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS launch_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT NOT NULL,
        project_desc TEXT,
        phase TEXT NOT NULL,
        yolo_zone TEXT NOT NULL DEFAULT 'test',
        max_agents INTEGER NOT NULL DEFAULT 11,
        init_only INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(self._SCHEMA)
            conn.execute(
                "INSERT OR IGNORE INTO yolo_state (id, zone, auto_approve, max_parallel) "
                "VALUES (1, 'safe', 0, 5)"
            )
            conn.commit()
            conn.close()

    def open(self):
        """Idempotent open — schema is already created in __init__.

        Provided for conftest compatibility (fixtures may call open/close
        lifecycle before/after tests).
        """
        pass

    def ensure_schema(self):
        """Idempotent schema creation — already done in _init_db.

        Provided for conftest compatibility.
        """
        pass

    def close(self):
        """No-op close — connections are short-lived per cursor() call.

        Provided for conftest compatibility.
        """
        pass

    @contextmanager
    def cursor(self):
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            try:
                yield c
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def log_event(self, kind: str, payload: dict = None):
        with self.cursor() as c:
            c.execute(
                "INSERT INTO event_log (kind, payload) VALUES (?, ?)",
                (kind, json.dumps(payload or {}))
            )


# ─── Phase Machine ───────────────────────────────────────────────

class PhaseStatus(Enum):
    TODO = "todo"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    ARCHIVED = "archived"
    BLOCKED = "blocked"

class PhaseMachine:
    ALL_PHASES = ["prd_build", "development", "quality", "hunting", "simplicity"]
    POINTS = {
        "prd_build": ["research", "build", "synthesize"],
        "development": ["architecture", "setup", "code_generation"],
        "quality": ["audit", "improve", "review"],
        "hunting": ["bugs", "arch_review", "security"],
        "simplicity": ["dead_code", "occam", "prd_alignment"],
    }

    def __init__(self, db: StateDB):
        self._db = db

    def start_phase(self, phase: str) -> PhaseEntry:
        if phase not in self.ALL_PHASES:
            raise ValueError(f"Unknown phase: {phase}. Valid: {self.ALL_PHASES}")
        now = datetime.utcnow().isoformat()
        with self._db.cursor() as c:
            c.execute(
                "INSERT INTO phase_state (phase, status, started_at, version) "
                "VALUES (?, 'running', ?, 1) "
                "ON CONFLICT(phase) DO UPDATE SET "
                "  status=COALESCE(NULLIF(status, 'done'), 'running'), "
                "  started_at=COALESCE(started_at, ?), "
                "  version=version+1",
                (phase, now, now)
            )
            c.execute("SELECT * FROM phase_state WHERE phase=?", (phase,))
            row = c.fetchone()
        self._db.log_event("phase_started", {"phase": phase})
        return PhaseEntry(**dict(row))

    def fail_phase(self, phase: str, reason: str = "") -> PhaseEntry:
        now = datetime.utcnow().isoformat()
        with self._db.cursor() as c:
            c.execute(
                "UPDATE phase_state SET status='failed', completed_at=?, version=version+1 "
                "WHERE phase=? AND status='running'",
                (now, phase)
            )
            if c.rowcount == 0:
                raise ConflictError(
                    f"Cannot fail phase '{phase}': not in running state"
                )
            c.execute("SELECT * FROM phase_state WHERE phase=?", (phase,))
            row = c.fetchone()
        self._db.log_event("phase_failed", {"phase": phase, "reason": reason})
        return PhaseEntry(**dict(row))

    def archive_phase(self, phase: str) -> PhaseEntry:
        with self._db.cursor() as c:
            c.execute(
                "UPDATE phase_state SET status='archived', version=version+1 "
                "WHERE phase=? AND (status='done' OR status='failed')",
                (phase,)
            )
            if c.rowcount == 0:
                raise ConflictError(
                    f"Cannot archive phase '{phase}': not done or failed"
                )
            c.execute("SELECT * FROM phase_state WHERE phase=?", (phase,))
            row = c.fetchone()
        self._db.log_event("phase_archived", {"phase": phase})
        return PhaseEntry(**dict(row))

    def complete_phase(self, phase: str) -> PhaseEntry:
        now = datetime.utcnow().isoformat()
        with self._db.cursor() as c:
            c.execute(
                "UPDATE phase_state SET status='done', completed_at=?, version=version+1 "
                "WHERE phase=? AND status='running'",
                (now, phase)
            )
            if c.rowcount == 0:
                raise ConflictError(
                    f"Cannot complete phase '{phase}': not in running state"
                )
            c.execute("SELECT * FROM phase_state WHERE phase=?", (phase,))
            row = c.fetchone()
        self._db.log_event("phase_completed", {"phase": phase})
        return PhaseEntry(**dict(row))

    def get_phase(self, phase: str) -> PhaseEntry | None:
        with self._db.cursor() as c:
            c.execute("SELECT * FROM phase_state WHERE phase=?", (phase,))
            row = c.fetchone()
            return PhaseEntry(**dict(row)) if row else None

    def all_phases(self) -> list[PhaseEntry]:
        with self._db.cursor() as c:
            c.execute("SELECT * FROM phase_state ORDER BY id")
            return [PhaseEntry(**dict(row)) for row in c.fetchall()]


# ─── Point Machine ───────────────────────────────────────────────

class PointMachine:
    def __init__(self, db: StateDB):
        self._db = db

    def create_point(self, phase: str, point: str, agent_count: int = 11) -> PointEntry:
        now = datetime.utcnow().isoformat()
        with self._db.cursor() as c:
            c.execute(
                "INSERT INTO point_state (phase, point, status, agent_count, started_at, version) "
                "VALUES (?, ?, 'todo', ?, NULL, 1) "
                "ON CONFLICT(phase, point) DO UPDATE SET "
                "  status='todo', "
                "  started_at=NULL, "
                "  completed_at=NULL, "
                "  version=version+1",
                (phase, point, agent_count)
            )
            c.execute("SELECT * FROM point_state WHERE phase=? AND point=?", (phase, point))
            row = c.fetchone()
        self._db.log_event("point_created", {"phase": phase, "point": point})
        return PointEntry(**dict(row))

    def start_point(self, phase: str, point: str) -> PointEntry:
        now = datetime.utcnow().isoformat()
        with self._db.cursor() as c:
            c.execute(
                "UPDATE point_state SET status='running', started_at=?, version=version+1 "
                "WHERE phase=? AND point=? AND status='todo'",
                (now, phase, point)
            )
            if c.rowcount == 0:
                raise ConflictError(
                    f"Cannot start point '{phase}/{point}': not in todo state"
                )
            c.execute("SELECT * FROM point_state WHERE phase=? AND point=?", (phase, point))
            row = c.fetchone()
        self._db.log_event("point_started", {"phase": phase, "point": point})
        return PointEntry(**dict(row))

    def complete_point(self, phase: str, point: str) -> PointEntry:
        now = datetime.utcnow().isoformat()
        with self._db.cursor() as c:
            c.execute(
                "UPDATE point_state SET status='done', completed_at=?, version=version+1 "
                "WHERE phase=? AND point=? AND (status='running' OR status='todo')",
                (now, phase, point)
            )
            if c.rowcount == 0:
                raise ConflictError(
                    f"Cannot complete point '{phase}/{point}': not running or todo"
                )
            c.execute("SELECT * FROM point_state WHERE phase=? AND point=?", (phase, point))
            row = c.fetchone()
        self._db.log_event("point_completed", {"phase": phase, "point": point})
        return PointEntry(**dict(row))

    def fail_point(self, phase: str, point: str, reason: str = "") -> PointEntry:
        now = datetime.utcnow().isoformat()
        with self._db.cursor() as c:
            c.execute(
                "UPDATE point_state SET status='failed', completed_at=?, version=version+1 "
                "WHERE phase=? AND point=? AND (status='running' OR status='todo')",
                (now, phase, point)
            )
            if c.rowcount == 0:
                raise ConflictError(
                    f"Cannot fail point '{phase}/{point}': not running or todo"
                )
            c.execute("SELECT * FROM point_state WHERE phase=? AND point=?", (phase, point))
            row = c.fetchone()
        self._db.log_event("point_failed", {"phase": phase, "point": point, "reason": reason})
        return PointEntry(**dict(row))

    def get_point(self, phase: str, point: str) -> PointEntry | None:
        with self._db.cursor() as c:
            c.execute("SELECT * FROM point_state WHERE phase=? AND point=?", (phase, point))
            row = c.fetchone()
            return PointEntry(**dict(row)) if row else None

    def get_points_for_phase(self, phase: str) -> list[PointEntry]:
        with self._db.cursor() as c:
            c.execute("SELECT * FROM point_state WHERE phase=? ORDER BY id", (phase,))
            return [PointEntry(**dict(row)) for row in c.fetchall()]

    def all_points(self) -> list[PointEntry]:
        with self._db.cursor() as c:
            c.execute("SELECT * FROM point_state ORDER BY id")
            return [PointEntry(**dict(row)) for row in c.fetchall()]


# ─── YOLO Machine ────────────────────────────────────────────────

YOLO_ZONES = {
    "safe":       {"auto_approve": False, "max_parallel": 5,   "max_errors": 3,   "desc": "Every action confirmed"},
    "test":       {"auto_approve": False, "max_parallel": 11,  "max_errors": 5,   "desc": "Limited parallel, confirm"},
    "staging":    {"auto_approve": True,  "max_parallel": 33,  "max_errors": 10,  "desc": "Auto-approve, moderate scale"},
    "production": {"auto_approve": True,  "max_parallel": 999, "max_errors": 999, "desc": "Full auto, max scale"},
}

class YOLOMachine:
    def __init__(self, db: StateDB):
        self._db = db

    def set_zone(self, zone: str) -> YOLOState:
        if zone not in YOLO_ZONES:
            raise ValueError(f"Unknown YOLO zone: {zone}")
        cfg = YOLO_ZONES[zone]
        with self._db.cursor() as c:
            c.execute(
                "UPDATE yolo_state SET zone=?, auto_approve=?, max_parallel=?, version=version+1 WHERE id=1",
                (zone, int(cfg["auto_approve"]), cfg["max_parallel"])
            )
            c.execute("SELECT * FROM yolo_state WHERE id=1")
            row = c.fetchone()
        self._db.log_event("yolo_zone_set", {"zone": zone})
        return YOLOState(**dict(row))

    def get_state(self) -> YOLOState:
        with self._db.cursor() as c:
            c.execute("SELECT * FROM yolo_state WHERE id=1")
            row = c.fetchone()
            return YOLOState(**dict(row)) if row else YOLOState()

    def increment_errors(self) -> YOLOState:
        with self._db.cursor() as c:
            c.execute("UPDATE yolo_state SET consecutive_errors = consecutive_errors + 1, version=version+1 WHERE id=1")
            c.execute("SELECT * FROM yolo_state WHERE id=1")
            row = c.fetchone()
        s = YOLOState(**dict(row))
        zone_cfg = YOLO_ZONES.get(s.zone, YOLO_ZONES["safe"])
        if s.consecutive_errors >= zone_cfg["max_errors"]:
            self.activate_safety_valve()
        return s

    def activate_safety_valve(self) -> YOLOState:
        with self._db.cursor() as c:
            c.execute("UPDATE yolo_state SET safety_valve_active=1, auto_approve=0, max_parallel=1, version=version+1 WHERE id=1")
            c.execute("SELECT * FROM yolo_state WHERE id=1")
            row = c.fetchone()
        self._db.log_event("safety_valve_activated", {})
        return YOLOState(**dict(row))

    def admit(self, current_runners: int, zone_name: str | None = None) -> bool:
        """Check whether a new runner may be admitted.

        Returns False if:
          - Safety valve is active, OR
          - current_runners >= max_parallel for the zone
        """
        state = self.get_state()
        zone = zone_name or state.zone
        zone_cfg = YOLO_ZONES.get(zone, YOLO_ZONES["safe"])
        if state.safety_valve_active:
            return False
        if current_runners >= zone_cfg["max_parallel"]:
            return False
        return True

    def reset_safety_valve(self) -> YOLOState:
        with self._db.cursor() as c:
            c.execute("UPDATE yolo_state SET safety_valve_active=0, consecutive_errors=0, version=version+1 WHERE id=1")
            c.execute("SELECT * FROM yolo_state WHERE id=1")
            row = c.fetchone()
        self._db.log_event("safety_valve_reset", {})
        return YOLOState(**dict(row))
