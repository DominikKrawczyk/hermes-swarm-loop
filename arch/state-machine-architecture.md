# State Machine Architecture — Phase, Point, and YOLO

## Overview

Hermes Swarm Loop uses three state machines to manage build pipeline execution.
Each is backed by **StateDB** (SQLite with WAL mode and version-based CAS) and
supports thread-safe transitions with event logging.

```
┌─────────────────────────────────────────────────────────────┐
│                    STATE MACHINE LAYER                        │
│                                                              │
│  ┌─────────────────┐    ┌─────────────────┐                  │
│  │   PhaseMachine  │    │   PointMachine  │                  │
│  │  ┌───────────┐  │    │  ┌───────────┐  │                  │
│  │  │ pending   │  │    │  │ pending   │  │                  │
│  │  │ running   │  │    │  │ running   │  │                  │
│  │  │ completed │  │    │  │ completed │  │                  │
│  │  │ failed    │  │    │  │ failed    │  │                  │
│  │  │ archived  │  │    │  └───────────┘  │                  │
│  │  └───────────┘  │    └─────────────────┘                  │
│  └─────────────────┘                                         │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │                  YOLOMachine                         │     │
│  │  ┌──────┐    ┌──────┐    ┌────────┐    ┌──────────┐ │     │
│  │  │ safe │───▶│ test │───▶│staging │───▶│production│ │     │
│  │  │  5   │    │  11  │    │   33   │    │   999    │ │     │
│  │  └──────┘    └──────┘    └────────┘    └──────────┘ │     │
│  │  Safety Valve: auto-engage on ≥5 consecutive errors  │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  All state machines backed by:                               │
│  ┌────────────────────────────────────────────────────┐      │
│  │  StateDB (SQLite + WAL)                           │      │
│  │  - Reentrant Lock (RLock) for thread safety       │      │
│  │  - Version-based CAS for conflict detection       │      │
│  │  - Append-only event log for audit trail          │      │
│  │  - All tables created with IF NOT EXISTS          │      │
│  └────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## PhaseMachine

### States

```
                    ┌──────────┐
                    │ pending  │  ← Phase created
                    └────┬─────┘
                         │ start_phase()
                         ▼
                    ┌──────────┐
              ┌────▶│ running  │◀────────┐
              │     └────┬─────┘         │
              │          │               │
              │    ┌─────┴─────┐         │
              │    │           │         │
              ▼    ▼           ▼         │
        ┌──────────┐     ┌──────────┐    │
        │completed │     │  failed  │    │ (loop back from
        └────┬─────┘     └────┬─────┘    │  simplicity phase)
             │                │          │
             ▼                ▼          │
        ┌──────────┐     ┌──────────┐    │
        │ archived │     │ archived │    │
        └──────────┘     └──────────┘    │
                                         │
    (Both completed and failed go to     │
     archived — terminal state)          │
                                         │
    Simplicity phase loops back to       │
    Development phase for next cycle     │
```

### Transition Rules

| From | To | Method | Notes |
|------|----|--------|-------|
| pending | running | `start_phase()` | |
| running | completed | `complete_phase()` | |
| running | failed | `fail_phase()` | Takes optional reason |
| completed | archived | `archive_phase()` | Terminal |
| failed | archived | `archive_phase()` | Terminal |
| _other_ | _anything_ | — | `ValueError` raised |

### CAS Conflict Detection

PhaseMachine uses `StateDB.update_with_cas()` which reads the row version,
compares with expected, and only writes if versions match. If another thread
modified the row between read and write, a `ConflictError` is raised.

---

## PointMachine

### States

```
                    ┌──────────┐
                    │ pending  │  ← Point created (via create_point())
                    └────┬─────┘
                         │ start_point()
                         ▼
                    ┌──────────┐
                    │ running  │  ← Agents working
                    └────┬─────┘
                         │
                    ┌────┴────┐
                    │         │
                    ▼         ▼
              ┌──────────┐ ┌──────────┐
              │completed │ │  failed  │
              └──────────┘ └──────────┘
              (terminal)    (terminal)
```

### Transition Rules

| From | To | Method | Notes |
|------|----|--------|-------|
| pending | running | `start_point()` | Sets started_at |
| running | completed | `complete_point()` | Sets completed_at |
| running | failed | `fail_point()` | Sets fail_reason in metadata |
| _other_ | _anything_ | — | `ConflictError` raised |

### CAS Implementation

PointMachine implements CAS at the SQL level:

```sql
UPDATE point_state
SET status = 'running', version = version + 1, started_at = ?
WHERE phase_name = ? AND name = ? AND version = ? AND status = 'pending'
```

If `rowcount == 0`, the update was either a version mismatch (CAS conflict) or
invalid state transition — both raise `ConflictError`.

### Events Logged

- `point_created` — payload: phase_name, point_name
- `point_started` — payload: phase_name, point_name
- `point_completed` — payload: phase_name, point_name
- `point_failed` — payload: phase_name, point_name, reason

---

## YOLOMachine

### Zones

```
                    Risk Level →
                    ────────────
    safe ◄──────── test ◄──────── staging ◄──────── production
  ┌─────────┐   ┌─────────┐    ┌─────────┐     ┌──────────┐
  │  max: 5 │   │ max: 11 │    │ max: 33 │     │ max: 999 │
  │ auto: F │   │ auto: T │    │ auto: T │     │ auto: T  │
  │ valve: Y│   │ valve: Y│    │ valve: N│     │ valve: N │
  │ err: 3  │   │ err: 5  │    │ err: 10 │     │ err: 999 │
  └─────────┘   └─────────┘    └─────────┘     └──────────┘
```

### Zone Definitions

| Zone | max_parallel | auto_approve | safety_valve | max_errors |
|------|-------------|--------------|--------------|------------|
| safe | 5 | False | Enabled | 3 |
| test | 11 | True | Enabled | 5 |
| staging | 33 | True | Disabled | 10 |
| production | 999 | True | Disabled | 999 |

### Safety Valve

When consecutive errors in safe or test zones reach the max_errors threshold,
the safety valve engages:

1. `safety_valve_active = True`
2. `admit()` returns `False` — no new agents can enter
3. Manual `reset_safety_valve()` required to clear
4. A `yolo.safety_valve_engaged` event is logged

### Admission Control

```python
def admit(self, current_runners: int, zone_name: str | None = None) -> bool:
    """Check whether a new runner may be admitted.

    Returns False if:
      - Safety valve is active, OR
      - current_runners >= max_parallel for the zone
    """
```

### Events Logged

- `yolo.zone_change` — payload: old_zone, new_zone, max_parallel, auto_approve
- `yolo.safety_valve_engaged` — payload: consecutive_errors, threshold
- `yolo.safety_valve_reset` — payload: {}

---

## StateDB — Common Backing Store

### Schema

```sql
TABLE phase_state (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    name             TEXT NOT NULL UNIQUE,
    status           TEXT NOT NULL DEFAULT 'pending',
    total_points     INTEGER NOT NULL DEFAULT 0,
    completed_points INTEGER NOT NULL DEFAULT 0,
    version          INTEGER NOT NULL DEFAULT 1,
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

TABLE point_state (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    phase_name    TEXT NOT NULL,
    name          TEXT NOT NULL,
    title         TEXT NOT NULL DEFAULT '',
    status        TEXT NOT NULL DEFAULT 'pending',
    agent_count   INTEGER NOT NULL DEFAULT 0,
    swarm_task_id TEXT NOT NULL DEFAULT '',
    started_at    TEXT NOT NULL DEFAULT '',
    completed_at  TEXT NOT NULL DEFAULT '',
    metadata      TEXT NOT NULL DEFAULT '{}',
    version       INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(phase_name, name)
);

TABLE yolo_state (
    id                  INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    zone                TEXT NOT NULL DEFAULT 'safe',
    auto_approve        INTEGER NOT NULL DEFAULT 0,
    max_parallel        INTEGER NOT NULL DEFAULT 5,
    safety_valve_active INTEGER NOT NULL DEFAULT 0,
    consecutive_errors  INTEGER NOT NULL DEFAULT 0,
    version             INTEGER NOT NULL DEFAULT 1,
    updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

TABLE event_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event       TEXT NOT NULL,
    payload     TEXT NOT NULL DEFAULT '{}',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Thread Safety Model

StateDB uses a **reentrant lock (RLock)** and exposes a context manager:

```python
with statedb as cursor:
    cursor.execute("SELECT ...")
    # cursor.rowcount works here
    # auto-commit on success, rollback on exception
```

This design ensures:
- One writer at a time
- Cursors are always from the same connection inside the context
- `cursor.rowcount` is available for CAS validation
- Auto-commit/rollback on exit
