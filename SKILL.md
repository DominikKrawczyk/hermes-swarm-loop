---
name: hermes-swarm-loop
description: "Phase 0: PRD BUILD 66 — Phase 1-3: 3 points × 11 agents each — Simplicity → Phase 0 — Cycle 1 BUILD, 2+ iterate"
version: 6.5.0
author: Edward Puszczyk
github: DominikKrawczyk
license: MIT
---

# Hermes Swarm Loop — 3 × 3 × 11

```
Phase 0: PRD BUILD — 66 agents (research + questions + 33+33) — one-time, until full PRD done
Phase 1: ARCHITECTURE 11 + SETUP 11 + CODE GENERATION 11
Phase 2: AUDIT 11 + IMPROVE 11 + REVIEW 11
Phase 3: BUGS 11 + ARCH 11 + SECURITY 11
Simplicity: Dead Code 11 + Occam 11 + PRD Alignment 11

Cycle 1: BUILD | Cycle 2+: iterate
Mastery Gate: diversified non-local per PRD area — check across all areas, not just one
Auto Skill Update: after each phase, skill learns & evolves
Gate: 11 per point | Forced points | Auto-detect | YOLO default ON | Scale 11→999
```

## Project Structure

```
/opt/hermes-swarm-loop/
├── SKILL.md                        # v6.4.0 — the framework definition
├── README.md                       # This file
├── PRD_Hermes_Swarm_Loop_v1.0.md   # Product Requirements Document
├── PRD_RAW_QUOTATIONS.md           # Raw user input (1:1 preserved)
├── bootstrap.py                    # 5-stage launcher (env, DB, phase, YOLO, launch)
├── Makefile                        # Test, install, lint, push targets
├── requirements.txt                # Python dependencies
├── launch.sh                       # Legacy launcher (superseded by bootstrap.py)
├── .gitignore
├── .github/workflows/test.yml      # CI: pytest + audit check
├── engine/                         # Core infrastructure (8 modules)
│   ├── __init__.py
│   ├── state_machine.py            # PhaseMachine, PointMachine, YOLOMachine (SQLite+WAL+CAS)
│   ├── mastery_gate.py             # 7-dimension quality gate (0.25/0.20/0.15/0.15/0.10/0.10/0.05)
│   ├── gate_verifier.py            # Gate verifier — validates 11-agent handoffs
│   ├── synthesizer.py              # Merge parallel agent outputs into coherent artifacts
│   ├── workspace_manager.py        # Scratch/dir/worktree lifecycle
│   ├── agent_roles.py              # 198 agent role definitions across all phases
│   └── config.py                   # Config loader (YAML/JSON with defaults)
├── scaling/                        # Scaling infrastructure (7 modules)
│   ├── __init__.py
│   ├── token_bucket.py             # Rate limiter (burst capacity + sustained rate)
│   ├── adaptive_batcher.py         # Batch items with back-pressure adaptation
│   ├── cas_store.py                # Compare-and-swap versioned KV store
│   ├── circuit_breaker.py          # Failure threshold + recovery (CLOSED/OPEN/HALF_OPEN)
│   ├── connection_pool.py          # Generic connection pool with health checks
│   ├── priority_queue.py           # Priority queue with time-based ageing
│   └── queue_pressure.py           # Monitor queue depth + throughput → LOW/NORMAL/HIGH/CRITICAL
├── configs/                        # Configuration files
│   ├── scaling_config.yaml         # Agent scaling, concurrency limits
│   ├── yolo_config.yaml            # YOLO zones (safe/test/staging/production)
│   └── logging_config.yaml         # Logging levels and handlers
├── scripts/                        # Utility scripts
│   └── init.sh                     # Quick venv + install + bootstrap
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── test_engine.py              # Phase/Point/YOLO state machine tests
│   ├── test_mastery_gate.py        # Mastery Gate scoring tests
│   └── test_all.py                 # All scaling + gate 11 tests
├── arch/                           # Architecture documents (from Phase 1 Pt1)
├── archive/                        # Archived old versions
├── deep-archive/
├── hunting/
├── launchers/
└── reflection/
```

## Phase 0 — PRD BUILD (66 agents, one-time)
66 agents: 33 research + 33 build. Runs until full PRD is complete.

→ Auto Skill Update: skill saves PRD structure and findings
→ **Mastery Gate**: diversified non-local check across all PRD areas

## Phase 1 — Development (3 points × 11 agents)
- ARCHITECTURE: architecture design
- SETUP: project setup
- CODE GENERATION: implementation start

→ Auto Skill Update: skill saves architecture decisions, setup patterns
→ **Mastery Gate**: cross-check arch decisions against PRD areas

## Phase 2 — Quality (3 points × 11 agents)
- AUDIT: code audit
- IMPROVE: improvements
- REVIEW: quality gate

→ Auto Skill Update: skill saves audit findings, improvement patterns
→ **Mastery Gate**: verify improvements don't break other PRD areas

## Phase 3 — Hunting (3 points × 11 agents)
- BUGS: bug hunting
- ARCH: architecture review
- SECURITY: security audit

→ Auto Skill Update: skill saves bug patterns, security rules
→ **Mastery Gate**: cross-check security/arch findings across domains

## Simplicity (3 points × 11 agents)
- Dead Code: consolidate, not destroy
- Occam: bottlenecks reduction
- PRD Alignment: gaps drive rebuild → Phase 0

→ Auto Skill Update: skill saves simplification rules
→ **Mastery Gate**: verify simplicity doesn't sacrifice PRD coverage

## Mastery Gate Logic
Not a simple pass/fail. For each PRD area, the gate spawns diversified checks across OTHER areas (non-local).

**Execution:** Spawn 1-3 cross-check agents via `delegate_task`. Each checks a different non-local area.
Score 7 dimensions (0-1): Correctness (0.25), Safety (0.20), Test Coverage (0.15), Consistency (0.15), Diversity (0.10), Efficiency (0.10), Clarity (0.05).
Thresholds: PASS ≥0.70, CROSS-CHECK 0.50-0.69, REVIEW 0.30-0.49, BLOCK <0.30.

## Bootstrap Launcher (`bootstrap.py`)

```bash
# Standard launch (development phase, test zone, 11 agents)
python3 bootstrap.py --project-name "MyApp" --project-desc "Build X"

# PRD BUILD phase with staging YOLO
python3 bootstrap.py --project-name "MyApp" --project-desc "Build X" \
  --phase prd_build --yolo-zone staging --max-agents 66

# Setup only (no launch commands printed)
python3 bootstrap.py --project-name "MyApp" --project-desc "Build X" --init-only
```

## Rules
- **Cycle 1: BUILD** — no iteration, just build from scratch
- **Cycle 2+: iterate** — self-reflection after each cycle
- **Forced points** — every point runs, no skipping
- **Gate 11** — verifier must pass before next point (under Mastery Gate)
- **Auto-detect** — project size auto-determines agent count (11/33/66/999)
- **YOLO default ON** — auto-approve ALL actions
- **Scale: 11→999** — no hard cap on agent count

## Disaster Recovery

If the VPS is rebuilt and the repo is gone:
1. `git clone https://github.com/DominikKrawczyk/hermes-swarm-loop.git ~/code/hermes-swarm-loop`
2. `python3 bootstrap.py --project-name "..." --project-desc "..." --init-only`
3. Push back to GitHub immediately after recovery

## Phase 1 Point 2 Completion (2026-06-02)

Project setup for Hermes Swarm Loop framework completed by 11 parallel agents.
**Artifacts created:**
- `bootstrap.py` — 5-stage launcher (env check, DB init, phase setup, YOLO init, launch)
- `engine/` — 8 modules: state_machine, mastery_gate, gate_verifier, synthesizer, workspace_manager, agent_roles, config, __init__
- `scaling/` — 7 production-grade concurrency primitives: token_bucket, adaptive_batcher, cas_store, circuit_breaker, connection_pool, priority_queue, queue_pressure
- `configs/` — scaling_config.yaml, yolo_config.yaml, logging_config.yaml
- `.github/workflows/` — test.yml (CI), lint.yml (ruff + mypy)
- `Makefile`, `requirements.txt`, `.gitignore`, `scripts/init.sh`
- `tests/conftest.py` — pytest fixtures
