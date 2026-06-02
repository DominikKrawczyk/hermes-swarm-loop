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
        self._lock = threading.RLock()
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
        """Idempotent open — schema is already created in __init__."""
        pass

    def ensure_schema(self):
        """Idempotent schema creation — already done in _init_db."""
        pass

    def close(self):
        """No-op close — connections are short-lived per cursor() call."""
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

    def _cas_update(self, phase: str, new_status: str, allowed_statuses: list[str],
                     set_clause: str = "", params: list | None = None) -> PhaseEntry:
        """CAS-protected update: read current version, update with WHERE version=? check.

        Raises ConflictError if the row is not in an allowed status or the version
        has changed since read (concurrent modification).
        """
        if params is None:
            params = []
        with self._db.cursor() as c:
            c.execute("SELECT version, status FROM phase_state WHERE phase=?", (phase,))
            row = c.fetchone()
            if row is None:
                raise ConflictError(f"Phase '{phase}' not found")
            current_version = row["version"]
            current_status = row["status"]
            if current_status not in allowed_statuses:
                raise ConflictError(
                    f"Cannot update phase '{phase}': status is '{current_status}', "
                    f"needs one of {allowed_statuses}"
                )
            extra_set = f", {set_clause}" if set_clause else ""
            c.execute(
                f"UPDATE phase_state SET status=?, version=version+1{extra_set} "
                f"WHERE phase=? AND version=?",
                (new_status, *params, phase, current_version)
            )
            if c.rowcount == 0:
                raise ConflictError(
                    f"CAS conflict updating phase '{phase}': version changed since read"
                )
            c.execute("SELECT * FROM phase_state WHERE phase=?", (phase,))
            return PhaseEntry(**dict(c.fetchone()))

    def start_phase(self, phase: str) -> PhaseEntry:
        if phase not in self.ALL_PHASES:
            raise ValueError(f"Unknown phase: {phase}. Valid: {self.ALL_PHASES}")
        now = datetime.utcnow().isoformat()
        with self._db.cursor() as c:
            c.execute(
                "INSERT OR IGNORE INTO phase_state (phase, status, started_at, version) "
                "VALUES (?, 'running', ?, 1)",
                (phase, now)
            )
            if c.rowcount == 1:
                # Insert succeeded — fresh row
                c.execute("SELECT * FROM phase_state WHERE phase=?", (phase,))
                row = c.fetchone()
            else:
                # Row already exists — need to update status, with CAS
                c.execute("SELECT version, status FROM phase_state WHERE phase=?", (phase,))
                row = c.fetchone()
                current_version = row["version"]
                current_status = row["status"]
                # Idempotent: if already running, return current state
                if current_status == "running":
                    c.execute("SELECT * FROM phase_state WHERE phase=?", (phase,))
                    row = c.fetchone()
                else:
                    # CAS update: transition to running with version guard
                    c.execute(
                        "UPDATE phase_state SET status='running', started_at=COALESCE(started_at, ?), "
                        "version=version+1 WHERE phase=? AND version=?",
                        (now, phase, current_version)
                    )
                    if c.rowcount == 0:
                        raise ConflictError(
                            f"Cannot start phase '{phase}': not in running state"
                        )
                    c.execute("SELECT * FROM phase_state WHERE phase=?", (phase,))
                    row = c.fetchone()
        self._db.log_event("phase_started", {"phase": phase})
        return PhaseEntry(**dict(row))

    def fail_phase(self, phase: str, reason: str = "") -> PhaseEntry:
        entry = self._cas_update(phase, "failed", ["running"],
                                  "completed_at=?", [datetime.utcnow().isoformat()])
        self._db.log_event("phase_failed", {"phase": phase, "reason": reason})
        return entry

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
            c.execute("SELECT version FROM phase_state WHERE phase=? AND status='running'", (phase,))
            row = c.fetchone()
            if row is None:
                raise ConflictError(
                    f"Cannot complete phase '{phase}': not in running state"
                )
            cur_version = row["version"]
            c.execute(
                "UPDATE phase_state SET status='done', completed_at=?, version=version+1 "
                "WHERE phase=? AND status='running' AND version=?",
                (now, phase, cur_version)
            )
            if c.rowcount == 0:
                raise ConflictError(
                    f"Cannot complete phase '{phase}': version conflict"
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
        with self._db.cursor() as c:
            c.execute(
                "INSERT INTO point_state (phase, point, status, agent_count, started_at, version) "
                "VALUES (?, ?, 'todo', ?, NULL, 1) "
                "ON CONFLICT(phase, point) DO UPDATE SET "
                "  status='todo', "
                "  started_at=NULL, "
                "  completed_at=NULL, "
                "  agent_count=excluded.agent_count, "
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
            c.execute("SELECT version FROM point_state WHERE phase=? AND point=? AND status='todo'",
                      (phase, point))
            row = c.fetchone()
            if row is None:
                raise ConflictError(
                    f"Cannot start point '{phase}/{point}': not in todo state"
                )
            cur_version = row["version"]
            c.execute(
                "UPDATE point_state SET status='running', started_at=?, version=version+1 "
                "WHERE phase=? AND point=? AND status='todo' AND version=?",
                (now, phase, point, cur_version)
            )
            if c.rowcount == 0:
                raise ConflictError(
                    f"Cannot start point '{phase}/{point}': version conflict"
                )
            c.execute("SELECT * FROM point_state WHERE phase=? AND point=?", (phase, point))
            row = c.fetchone()
        self._db.log_event("point_started", {"phase": phase, "point": point})
        return PointEntry(**dict(row))

    def complete_point(self, phase: str, point: str) -> PointEntry:
        now = datetime.utcnow().isoformat()
        with self._db.cursor() as c:
            c.execute("SELECT version FROM point_state WHERE phase=? AND point=? "
                      "AND (status='running' OR status='todo')", (phase, point))
            row = c.fetchone()
            if row is None:
                raise ConflictError(
                    f"Cannot complete point '{phase}/{point}': not running or todo"
                )
            cur_version = row["version"]
            c.execute(
                "UPDATE point_state SET status='done', completed_at=?, version=version+1 "
                "WHERE phase=? AND point=? AND (status='running' OR status='todo') AND version=?",
                (now, phase, point, cur_version)
            )
            if c.rowcount == 0:
                raise ConflictError(
                    f"Cannot complete point '{phase}/{point}': version conflict"
                )
            c.execute("SELECT * FROM point_state WHERE phase=? AND point=?", (phase, point))
            row = c.fetchone()
        self._db.log_event("point_completed", {"phase": phase, "point": point})
        return PointEntry(**dict(row))

    def fail_point(self, phase: str, point: str, reason: str = "") -> PointEntry:
        now = datetime.utcnow().isoformat()
        with self._db.cursor() as c:
            c.execute("SELECT version FROM point_state WHERE phase=? AND point=? "
                      "AND (status='running' OR status='todo')", (phase, point))
            row = c.fetchone()
            if row is None:
                raise ConflictError(
                    f"Cannot fail point '{phase}/{point}': not running or todo"
                )
            cur_version = row["version"]
            c.execute(
                "UPDATE point_state SET status='failed', completed_at=?, version=version+1 "
                "WHERE phase=? AND point=? AND (status='running' OR status='todo') AND version=?",
                (now, phase, point, cur_version)
            )
            if c.rowcount == 0:
                raise ConflictError(
                    f"Cannot fail point '{phase}/{point}': version conflict"
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

    def _cas_update_yolo(self, set_clause: str, params: list | None = None) -> YOLOState:
        """CAS-protected update for the singleton yolo_state row (id=1)."""
        if params is None:
            params = []
        with self._db.cursor() as c:
            c.execute("SELECT version FROM yolo_state WHERE id=1")
            row = c.fetchone()
            if row is None:
                raise ConflictError("YOLO state row not found")
            current_version = row["version"]
            c.execute(
                f"UPDATE yolo_state SET {set_clause}, version=version+1 WHERE id=1 AND version=?",
                (*params, current_version)
            )
            if c.rowcount == 0:
                raise ConflictError(
                    "CAS conflict updating YOLO state: version changed since read"
                )
            c.execute("SELECT * FROM yolo_state WHERE id=1")
            return YOLOState(**dict(c.fetchone()))

    def set_zone(self, zone: str) -> YOLOState:
        if zone not in YOLO_ZONES:
            raise ValueError(f"Unknown YOLO zone: {zone}")
        cfg = YOLO_ZONES[zone]
        entry = self._cas_update_yolo(
            "zone=?, auto_approve=?, max_parallel=?",
            [zone, int(cfg["auto_approve"]), cfg["max_parallel"]]
        )
        self._db.log_event("yolo_zone_set", {"zone": zone})
        return entry

    def get_state(self) -> YOLOState:
        with self._db.cursor() as c:
            c.execute("SELECT * FROM yolo_state WHERE id=1")
            row = c.fetchone()
            return YOLOState(**dict(row)) if row else YOLOState()

    def increment_errors(self) -> YOLOState:
        entry = self._cas_update_yolo("consecutive_errors = consecutive_errors + 1")
        zone_cfg = YOLO_ZONES.get(entry.zone, YOLO_ZONES["safe"])
        if entry.consecutive_errors >= zone_cfg["max_errors"]:
            self.activate_safety_valve()
        return entry

    def activate_safety_valve(self) -> YOLOState:
        entry = self._cas_update_yolo(
            "safety_valve_active=1, auto_approve=0, max_parallel=1"
        )
        self._db.log_event("safety_valve_activated", {})
        return entry

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
        entry = self._cas_update_yolo(
            "safety_valve_active=0, consecutive_errors=0"
        )
        self._db.log_event("safety_valve_reset", {})
        return entry
