# Hermes Swarm Loop — Architecture Overview

**Version:** 6.10.0
**Author:** Edward Puszczyk (github: DominikKrawczyk)
**License:** MIT

## Overview

The Hermes Swarm Loop is a **4-phase × 3-point × 11-agent** autonomous build framework
for AI-powered software development. It orchestrates parallel Hermes Agent workers
through a structured pipeline of phases, points, and gates to build anything from
blockchain infrastructure to complex applications.

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    HERMES SWARM LOOP                             │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │
│  │  PHASE 1 │   │  PHASE 2 │   │  PHASE 3 │   │  PHASE 4 │     │
│  │ PRD BUILD│──▶│DEVELOPMENT│──▶│ HUNTING  │──▶│ QUALITY  │     │
│  │ (66 ag)  │   │ (33 ag)  │   │ (33 ag)  │   │ (33 ag)  │     │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘     │
│                                           │                     │
│                                           ▼                     │
│                                  ┌──────────────┐               │
│                                  │   PHASE 5    │               │
│                                  │  SIMPLICITY  │               │
│                  ┌───────────────│   (33 ag)    │───────────────┘
│                  │               └──────────────┘
│                  │                       │
│                  └───────────────────────┘
│                          (loops back to Phase 2)
│
│  Each Phase contains 3 Points × 11 agents each (default)
│  After each point: Mastery Gate + Verifier check
└─────────────────────────────────────────────────────────────────┘
```

## Core Architecture

### Three Pillars

```
┌─────────────────────────────────────────────────────────────┐
│                    HERMES SWARM LOOP                          │
├─────────────────┬───────────────────┬───────────────────────┤
│                 │                   │                       │
│     Engine      │     Scaling       │    Configuration      │
│  ┌───────────┐  │  ┌─────────────┐  │  ┌─────────────────┐  │
│  │ StateDB   │  │  │ TokenBucket │  │  │ agent_roles.yaml│  │
│  │ PhaseMachine│  │  │ CASStore   │  │  │ scaling.yaml   │  │
│  │ PointMachine│  │  │ CircuitBrkr│  │  │ yolo.yaml      │  │
│  │ YOLOMachine │  │  │ ConnPool   │  │  │ workspace.yaml │  │
│  │ MasteryGate │  │  │ AdaptBatch │  │  │ bootstrap.json │  │
│  │ GateVerifier│  │  │ PriorityQ  │  │  └─────────────────┘  │
│  └───────────┘  │  │ QueuePress  │  │                       │
│                 │  └─────────────┘  │                       │
├─────────────────┴───────────────────┴───────────────────────┤
│                                                              │
│  Bootstrap CLI ────► State Machines ────► Mastery Gate       │
│       │                    │                    │            │
│       ▼                    ▼                    ▼            │
│  Config File          SQLite DB             Verdict          │
│  (JSON/YAML)          (WAL mode)       (PASS/CHECK/REV/BLK) │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow

```
User CLI (bootstrap.py)
     │
     ▼
┌──────────┐    ┌──────────────┐    ┌────────────┐
│  Config  │───▶│  StateDB     │◀───│  Engine    │
│  Files   │    │  (SQLite)    │    │  Modules   │
└──────────┘    └──────┬───────┘    └────────────┘
                       │
                       ▼
               ┌───────────────┐
               │  Event Log    │
               │  (append-only) │
               └───────────────┘
                       │
                       ▼
               ┌───────────────┐
               │  Mastery Gate │───▶ Verdict
               │  (7 dims)    │     (PASS/CROSS-CHECK/REVIEW/BLOCK)
               └───────────────┘
                       │
                       ▼
               ┌───────────────┐
               │  Scaling      │───▶ Token Bucket → Circuit Breaker
               │  Layer        │     → Connection Pool → Batcher
               └───────────────┘
```

## Component Roles

| Component | Role |
|-----------|------|
| **StateDB** | SQLite-backed state store with WAL mode, thread-safe cursor-based access, version-based CAS (optimistic locking) |
| **PhaseMachine** | Manages phase lifecycle: pending → running → completed/failed → archived |
| **PointMachine** | Manages point lifecycle within phases: pending → running → completed/failed |
| **YOLOMachine** | Zone management (safe/test/staging/production) with safety valve auto-pause |
| **MasteryGate** | 7-dimension scoring (completeness, correctness, coverage, consistency, clarity, confidence, novelty) → 4 verdict paths |
| **GateVerifier** | Schema-based handoff validation between points/phases |
| **TokenBucket** | Rate limiter for controlling agent spawn pace |
| **CircuitBreaker** | Failure isolation with half-open recovery |
| **ConnectionPool** | Reusable connection lifecycle management |
| **AdaptiveBatcher** | Dynamic batch sizing based on latency feedback |
| **PriorityQueue** | Priority-sorted task queue with aging to prevent starvation |
| **QueuePressure** | Backpressure monitoring and throttling |
| **WorkspaceManager** | Scratch/dir/worktree workspace lifecycle |

## Thread Safety

All state machines use **StateDB's reentrant lock (RLock)** for serialized writes
and **version-based compare-and-swap (CAS)** for conflict detection. This ensures:

- No concurrent write corruption
- Safe cursor operations across coroutines
- Retry on conflict via `update_with_cas()`

## File Layout

```
/opt/hermes-swarm-loop/
├── bootstrap.py              # CLI entry point
├── engine/                   # Core state machines
│   ├── state_db.py           # SQLite backing store
│   ├── phase_machine.py      # Phase lifecycle
│   ├── point_machine.py      # Point lifecycle
│   ├── yolo_machine.py       # YOLO zone management
│   ├── mastery_gate.py       # 7-dim scoring & verdict
│   ├── gate_verifier.py      # Handoff validation
│   └── gate_11.py            # 11-agent gate verifier
├── scaling/                  # Scaling layer
│   ├── token_bucket.py       # Rate limiting
│   ├── adaptive_batcher.py   # Batch sizing
│   ├── cas_store.py          # CAS state store
│   ├── circuit_breaker.py    # Failure isolation
│   ├── connection_pool.py    # Connection reuse
│   ├── priority_queue.py     # Priority queue
│   └── queue_pressure.py     # Backpressure
├── configs/                  # YAML configuration
│   ├── agent_roles.yaml
│   ├── scaling.yaml
│   ├── yolo.yaml
│   └── workspace.yaml
├── tests/                    # Test suite
│   ├── conftest.py
│   ├── test_state_machine.py
│   ├── test_mastery_gate.py
│   ├── test_scaling.py
│   └── test_bootstrap.py
└── arch/                     # Architecture docs
    ├── architecture-overview.md
    ├── state-machine-architecture.md
    ├── mastery-gate-spec.md
    ├── scaling-infrastructure.md
    ├── workspace-manager-spec.md
    ├── yolo-zones.md
    └── agent-roles.md
```
