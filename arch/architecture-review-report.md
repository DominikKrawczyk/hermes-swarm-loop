# Architecture Review Report — Hermes Swarm Loop

**Phase 3 Point 2: Architecture Review**
**Date:** 2026-06-02
**Codebase:** Hermes Swarm Loop v6.5.1 (at /opt/hermes-swarm-loop/)
**Architecture documents audited:** architecture-overview.md, state-machine-architecture.md, mastery-gate-spec.md, scaling-infrastructure.md, workspace-manager-spec.md, yolo-zones.md, agent-roles.md
**Code audited:** engine/ (state_machine.py, mastery_gate.py, workspace_manager.py, config.py, gate_11.py, gate_verifier.py), scaling/ (all 7 modules), configs/
**Baseline audit:** arch/audit-report.md (17 bugs fixed, 390/390 tests)

---

## Executive Summary

**13 architecture-to-code inconsistencies found** across 7 architecture documents. **2 design debt items.** **1 missing abstraction.** **2 over-engineering items.** The existing architecture review report (predecessor of this one) covered 11 findings but had 2 factual inaccuracies and missed 3 additional inconsistencies. This report corrects those and adds the missing findings.

The architecture documents were written at v6.4.0, before any code was generated. They describe a planned design that diverged from what Phase 1 agents actually built. None of the documents have been updated through Phases 1, 2, or 3 Point 1. The code is functionally sound (390/390 tests pass, 17 bugs fixed), but the docs are a pre-implementation blueprint, not a post-implementation reference.

---

## Findings

### 1. CRITICAL: Mastery Gate Dimension Names, Weights, and Thresholds — Completely Wrong

Seven different dimension names. Different weights. Different verdict thresholds. The arch doc and the actual code share zero dimension names.

| Aspect | Mastery-gate-spec.md (arch) | Actual code (mastery_gate.py + config.yaml) |
|--------|-----------------------------|---------------------------------------------|
| Dim 1 | completeness (0.20) | correctness (0.25) |
| Dim 2 | correctness (0.20) | safety (0.20) |
| Dim 3 | coverage (0.15) | test_coverage (0.15) |
| Dim 4 | consistency (0.15) | consistency (0.15) ✓ |
| Dim 5 | clarity (0.10) | diversity (0.10) |
| Dim 6 | confidence (0.10) | efficiency (0.10) |
| Dim 7 | novelty (0.10) | clarity (0.05) |
| PASS | >= 0.85 | >= 0.70 |
| CROSS-CHECK | >= 0.70 | >= 0.50 |
| REVIEW | >= 0.50 | >= 0.30 |
| BLOCK | < 0.50 | < 0.30 |

A score of 0.72 with all dims >= 0.50 produces REVIEW (blocked) per the arch doc, but CROSS-CHECK (auto-advance) in actual code. Decisions made by reading the arch doc are wrong.

The MasteryScore/ScoreCard API is also completely different. The arch doc describes a `MasteryScore` class with `get_weighted_score()`, `get_min_score()`, `get_weakest_dimension()`, and `set_dimension()` methods. The actual code uses a `ScoreCard` dataclass with `weighted_total` and `verdict` properties. No `GateResult` dataclass. No `Verdict` enum. The `MasteryGate.__init__()` signature is `(prd_areas=None, diversification_threshold=0.5)` — completely different from the doc's threshold-per-constructor-param design.

Audit-report.md bug #6 flagged the `check_diversification` method only checked 3 of 7 dims. That was fixed in code but the arch doc was never touched.

**Fix:** Rewrite mastery-gate-spec.md to match the actual v6.5.1 implementation: dimensions = correctness/safety/test_coverage/consistency/diversity/efficiency/clarity, weights = 0.25/0.20/0.15/0.15/0.10/0.10/0.05, thresholds = 0.70/0.50/0.30.

---

### 2. HIGH: File Structure — Modular Design Documented, Monolith Implemented

The architecture docs (architecture-overview.md and state-machine-architecture.md) describe four separate files:
```
engine/
├── state_db.py         # SQLite backing store
├── phase_machine.py    # Phase lifecycle
├── point_machine.py    # Point lifecycle
└── yolo_machine.py     # YOLO zone management
```

The actual code has everything in one 535-line file:
```
engine/
└── state_machine.py     # StateDB + PhaseMachine + PointMachine + YOLOMachine
```

Anyone reading the arch docs to understand the codebase will expect modular files and find a monolith instead. Makes the docs misleading for onboarding.

**Fix:** Either split state_machine.py into the documented files (low effort, high maintainability gain) or update the docs to describe the monolith. The refactor is mechanical: each class is self-contained with clear boundaries.

---

### 3. HIGH: Scaling Infrastructure — All 7 Modules Are Unwired (Not Just 5)

The scaling-infrastructure.md describes an elegant integration flow: TokenBucket → PriorityQueue → QueuePressure → AdaptiveBatch → ConnPool → CircuitBreaker → Agent spawned.

Reality: **zero** scaling modules are imported by runtime code. All 7 — TokenBucket, AdaptiveBatcher, CASStore, CircuitBreaker, ConnectionPool, PriorityQueue, QueuePressure — appear only in test fixtures (conftest.py) and test_scaling.py. Not one is imported by engine/, bootstrap.py, __main__.py, or the CLI.

The previous review report claimed CASStore and ConnectionPool had "active runtime consumers." This is incorrect. A search across all non-test .py files found zero imports of any scaling module. They are a futures bet, not live infrastructure.

The arch doc also describes CASStore as a SQLite-backed store with `retry_on_conflict=3`, `lock_timeout_ms=5000`, WAL mode, and an `update(key, transform)` method. The actual CASStore is a pure in-memory dict with threading.RLock — no SQLite, no retry, no `update()` method. It can't survive a process restart.

**Impact:** ~1,340 lines of well-tested, well-documented code that nobody calls. If these modules stay unwired through the next cycle, the Simplicity phase should consider removing them.

**Fix:** Either wire them into the runtime (bootstrap.py or the CLI) or update scaling-infrastructure.md to describe them as "available but not yet integrated."

---

### 4. MEDIUM: State Names — "pending" vs "todo"

All state diagrams in state-machine-architecture.md show the initial point state as "pending." The actual code uses "todo" throughout — in the `PointEntry` dataclass (`status: str = "todo"`), in `create_point()` (`SET status='todo'`), and in `start_point()` (`WHERE status='todo'`).

**Impact:** Anyone parsing state from the DB or writing state-machine consumers based on the arch doc will look for "pending" and find nothing. The `PhaseEntry` dataclass also uses "todo" as default.

**Fix:** Replace "pending" with "todo" in all state diagrams and transition rules in state-machine-architecture.md.

---

### 5. MEDIUM: YOLO Zone auto_approve — Triple Inconsistency

There are now **three sources** of truth for YOLO zone config, and they don't agree:

| Source | test auto_approve | staging safety_valve_enabled |
|--------|------------------|------------------------------|
| yolo-zones.md (arch doc) | True | Disabled |
| yolo_config.yaml | False | True |
| engine/state_machine.py YOLO_ZONES | False | (not in zone schema) |
| **config.yaml** | **True** | (not in this file's schema) |

The audit (#4) fixed the code/config mismatch between yolo_config.yaml and state_machine.py (both now say False). But config.yaml at line 37 still says `test: {auto_approve: true}`, and the arch doc yolo-zones.md still says True. That's a 4-way inconsistency where 3 sources say True and 2 say False (some overlap since yolo_config.yaml and state_machine.py agree).

Since the CLI loads config.yaml (via cli.py:93), the config.yaml value matters at runtime.

**Fix:** Set `test.auto_approve: false` in config.yaml (line 37). Update yolo-zones.md test zone auto_approve to False. All three live configs should agree with the code.

---

### 6. MEDIUM: Workspace API Surface — Method Names Don't Match

The workspace-manager-spec.md documents:
- `create(task_id, kind, workspace_path)` — not in code
- `destroy(workspace)` — not in code
- `resolve_path(workspace, *parts)` — not in code
- `Workspace.is_ready: bool` (field) — computed property in code, not a stored field

The actual code has:
- `setup(kind, *, task_id, dir_path, branch, label)` — different name + kwarg-only
- `teardown(workspace, *, cleanup=True)` — different name
- `resolve_kind_from_token(token)` — not documented
- `resolve_path_from_token(token)` — not documented
- `current_task_workspace(task_id)` — not documented
- `list_active()` — not documented
- `Workspace.is_git_worktree, branch, label, metadata` — not in the arch doc's dataclass

**Fix:** Update workspace-manager-spec.md to match the actual API. The implementation is clean and well-documented — the docs just describe a different API.

---

### 7. MEDIUM: Phase Flow Diagram — Shows Wrong Cycle Pattern

The architecture-overview.md shows a linear 5-phase flow (Phase 0→1→2→3→4 with a simplicity loop back to Phase 2). The SKILL.md describes the actual pattern: Phase 0 one-time, then Phase 1 (once) → Phase 2 → Phase 3 with a quality swap loop between Quality ↔ Hunting. Simplicity is an optional separate pass, not part of the main cycle.

**Impact:** Anyone planning capacity or scheduling work based on the arch diagram will expect a 5-phase linear pipeline with no swap loop.

**Fix:** Update the high-level flow diagram to match the SKILL.md's 3-phase swap pattern.

---

### 8. MEDIUM: gate_verifier.py vs gate_11.py — Duplicate with Deprecation

The arch doc (architecture-overview.md file layout) lists `gate_verifier.py` and `gate_11.py` as distinct components. In the code, `gate_verifier.py` has a deprecation notice at line 5: "This module is superseded by engine.gate_11 (Gate11Verifier)."

`gate_verifier.py` (133 lines) has a full `GateVerifier` class with `HandoffSchema`, `HandoffValidationResult`, `AgentCompletionStatus` enum, and JSON schema validation. `gate_11.py` (124 lines) has a simpler `Gate11Verifier` with `HandoffValidation` and `GateResult`.

These have overlapping functionality. The arch doc doesn't mention the deprecation or explain when to use which.

**Fix:** Either remove gate_verifier.py (it's deprecated) and update the file layout, or document the deprecation in the arch docs.

---

### 9. MEDIUM: config.yaml Version — Still 6.4.0

config.yaml line 7: `version: "6.4.0"`. pyproject.toml line 7: `version = "6.5.1"`. The audit (#14) bumped pyproject.toml from 6.4.0 to 6.5.1 but missed config.yaml. This is the runtime configuration file loaded by the CLI.

Also, architecture-overview.md:3 says "Version: 6.4.0".

**Fix:** Set `version: "6.5.1"` in config.yaml line 7 and update architecture-overview.md.

---

### 10. LOW: config.yaml test auto_approve=true — Unchecked Inconsistency

See finding #5. This affects the runtime since the CLI loads config.yaml. If the runtime uses config.yaml's zone config, `test` zone would have `auto_approve: true` while `engine/state_machine.py:YOLO_ZONES` says `false`. This is the same bug the audit (#4) fixed in yolo_config.yaml but missed in config.yaml.

**Fix:** `config.yaml` line 37: change `auto_approve: true` to `auto_approve: false` for the test zone.

---

### 11. LOW: SKILL.md References Non-Existent logging_config.yaml

SKILL.md line 60 lists `logging_config.yaml` as an active config file under configs/. The file was moved to `configs/archive/logging_config.yaml` during the Phase 2 Point 2 config cleanup (7 files removed). The only active config files are config.yaml, scaling_config.yaml, and yolo_config.yaml.

**Fix:** Update SKILL.md to list the correct active config files.

---

### 12. LOW: Agent Roles — 14 Documented vs 198 Autogenerated

agent-roles.md describes 14 well-defined roles. The actual code (engine/agent_roles.py) has 198 autogenerated entries sharing only 33 distinct descriptions. The agent_roles.yaml config file was deleted in Phase 2 Point 2 as dead code. The role definition in agent-roles.md doesn't describe the actual generation mechanism.

**Fix:** Either remove agent-roles.md (roles are dynamically generated) or update it to describe the autogeneration pattern.

---

### 13. LOW: Architecture Overview Lists Tests Incompletely

The file layout section (architecture-overview.md:154-159) lists 4 test files:
```
├── tests/
│   ├── test_state_machine.py
│   ├── test_mastery_gate.py
│   ├── test_scaling.py
│   └── test_bootstrap.py
```

Actual test files include 7 more: test_integration.py, test_config.py, test_agent_roles.py, test_synthesizer.py, test_gate_11.py, test_workspace_manager.py, test_synthesizer2.py.

**Fix:** Update the file layout to list all test files.

---

### Additional: config.yaml Has No Runtime Consumer

config.yaml is loaded by cli.py:93-95 and configs/__init__.py documents it as "main project config (loaded by CLI)". But the config.yaml values (phase structure, version, YOLO zones, Mastery Gate weights, database settings, workspace config, scaling settings, runtime settings) are not used by the actual state machine runtime. The state machine has its own hardcoded `ALL_PHASES`, `POINTS`, `YOLO_ZONES` in state_machine.py. The mastery gate has its own `DIMENSIONS` in mastery_gate.py. The config.py loader provides defaults that can be overridden, but the actual runtime code doesn't import config values.

This means config.yaml is a documentation file that happens to have a loader, but no reader. The `load_config()` function returns defaults unless a file is found, and the engine code doesn't call `load_config()` for runtime values.

---

## Design Debt

### D1: State Machine Monolith (535 Lines, 4 Classes)

All three state machines + DB layer live in one file. The arch docs show a clean modular design. The code works and is well-tested, but single-file monoliths grow fragile. Every mutation method needed CAS guards added during the audit — a refactor would have contained the blast radius per class.

**Severity:** MEDIUM
**Fix:** Split into `state_db.py`, `phase_machine.py`, `point_machine.py`, `yolo_machine.py` with `state_machine.py` as re-exports for backward compat.

### D2: CASStore In-Memory — No Process-Safe Persistence

The arch doc describes a SQLite-backed CASStore; the actual implementation is in-memory dict. State is lost on restart. Only thread-safe, not process-safe. The `ConflictError` class and `CasEntry` class are dead code in cas_store.py (never raised/used by runtime code).

**Severity:** MEDIUM-HIGH
**Fix:** Implement SQLite-backed CASStore as the arch doc describes, or remove dead code (CasEntry, ConflictError).

---

## Missing Abstractions

### M1: No Formal Phase↔Point Dependency Graph

Phases and points are independent tables linked by name strings. The PhaseMachine tracks `completed_points` as a counter, not a set of specific point IDs. There's no way for an agent to discover "which POINT_A depends on POINT_B." The dependency is implicit (correct sequencing in bootstrap). A `depends_on` column in point_state would enable graph-based resolution.

**Severity:** LOW (bootstrap is deterministic, no bugs from this)
**Fix:** Add `depends_on TEXT` column to point_state. Optional for backward compat.

---

## Over-Engineering

### O1: 1,340 Lines of Unwired Scaling Infrastructure

7 modules, 1,340 lines of code, all only exercised by tests. TokenBucket (208 lines), AdaptiveBatcher (197), CASStore (125), CircuitBreaker (209), ConnectionPool (313), PriorityQueue (174), QueuePressure (118). None imported by any runtime code path. The arch doc integration flow diagram is aspirational.

**Severity:** LOW (tested code has no bugs — it's just unused)
**Fix:** Wire into runtime or consolidate.

### O2: Two Gate Verifier Implementations

gate_verifier.py (deprecated, 133 lines) and gate_11.py (active, 124 lines) overlap in functionality. The deprecated one has richer features (JSON schema validation, agent status enum) but is marked for removal. Keeping both creates confusion and doubles maintenance surface.

**Severity:** LOW
**Fix:** Remove gate_verifier.py, promote gate_11.py's simpler interface.

---

## Summary Table

| # | Category | Severity | Description | Fix |
|---|----------|----------|-------------|-----|
| 1 | Mastery Gate | CRITICAL | 7 different dim names/weights/thresholds, different API | Rewrite mastery-gate-spec.md |
| 2 | File Structure | HIGH | Arch doc says 4 files; code has 1 monolith | Split state_machine.py or update docs |
| 3 | Scaling Infra | HIGH | ALL 7 scaling modules unwired; CASStore is in-memory not SQLite | Wire in or update docs |
| 4 | State Names | MEDIUM | "pending" in arch vs "todo" in code | Update state-machine-architecture.md |
| 5 | YOLO Config | MEDIUM | 4-way inconsistency: config.yaml says True, code says False | Fix config.yaml, update yolo-zones.md |
| 6 | Workspace API | MEDIUM | create/destroy vs setup/teardown | Update workspace-manager-spec.md |
| 7 | Phase Flow | MEDIUM | 5-phase linear vs 3-phase swap | Update architecture-overview.md |
| 8 | Gate Duplicate | MEDIUM | gate_verifier.py deprecated but in arch doc | Remove or document deprecation |
| 9 | Version | MEDIUM | config.yaml=6.4.0, pyproject.toml=6.5.1, arch doc=6.4.0 | Set all to 6.5.1 |
| 10 | config.yaml YOLO | LOW | auto_approve=true for test zone, disagrees with code | Change to false in config.yaml |
| 11 | SKILL.md listing | LOW | Lists non-existent logging_config.yaml | Update file listing |
| 12 | Agent Roles | LOW | 14 doc roles vs 198 autogenerated | Remove or update agent-roles.md |
| 13 | Test list | LOW | Arch doc lists 4 test files; 11 exist | Update file layout |

---

## Cross-Reference with Audit Report (arch/audit-report.md)

The Phase 2 Point 1 audit found 17 bugs across ~6,500 lines. The architecture-relevant ones:

| Bug # | Bug | Architecture Impact | Reflected in Arch Docs? |
|-------|-----|--------------------|------------------------|
| 1 | CAS version guard missing on all 12 mutation methods | StateMachine thread safety | Not reflected — docs describe CAS but don't show WHERE version=? |
| 4 | YOLO test zone auto_approve mismatch | Config vs code disagreement | Not reflected (finding #5 above) |
| 6 | MasteryGate check_diversification only 3 of 7 dims | Gate scoring incomplete | Not reflected (finding #1 — dimension set entirely different) |
| 7 | reset_safety_valve doesn't restore zone defaults | YOLO zone behavior broken | Not reflected — docs don't describe this behavior |
| 9 | MasteryGate empty-list falsy `or` bug | Edge case in gate | Not reflected |
| 14 | pyproject.toml version drift 6.4.0→6.5.1 | Version tracking | Partially — arch doc still says 6.4.0 |

**All 17 bugs are fixed in code.** None are reflected in the architecture documents. The architecture docs describe a pre-implementation v6.4.0 design that predates all bug fixes and implementation choices.

---

## Recommendations

### Before next cycle (high priority)
1. **Rewrite mastery-gate-spec.md** — replace all dimension names, weights, thresholds, and API references to match the actual ScoreCard/MasteryGate implementation
2. **Fix config.yaml** — set `test: auto_approve: false` (line 37) and `version: "6.5.1"` (line 7)
3. **Fix state-machine-architecture.md** — replace "pending" with "todo" in all diagrams
4. **Fix yolo-zones.md** — set test zone auto_approve to False

### Short-term
5. **Update architecture-overview.md** — fix file layout, phase flow diagram, version number, and test file listing
6. **Update workspace-manager-spec.md** — fix API reference to match setup/teardown/current_task_workspace
7. **Update scaling-infrastructure.md** — describe CASStore as in-memory, acknowledge all 7 modules are unwired
8. **Remove gate_verifier.py** or document deprecation clearly in arch docs
9. **Update SKILL.md** — fix configs listing (remove logging_config.yaml)

### Medium-term
10. **Split state_machine.py** into the documented 4-file modular structure
11. **Wire scaling modules** into the runtime or move them to a /contrib/ directory
12. **Implement SQLite-backed CASStore** for process-safe persistence

---

## Incorrect Assumptions in Previous Architecture Review Report

The predecessor of this report (same path, overwritten by this version) had two factual errors that this report corrects:

1. **"CASStore and ConnectionPool have active runtime consumers"** — Incorrect. All 7 scaling modules appear exclusively in test code. None are imported by any runtime module.

2. **"Cross-reference with bug-report.md"** — No bug-report.md exists at the referenced path. Bug findings are consolidated into audit-report.md.

---

## Conclusion

The code is solid: 390/390 tests pass, 17 bugs fixed, no circular dependencies, no god objects. The architecture documents are stale — they describe a v6.4.0 plan that predates the actual implementation. The most urgent fix is the Mastery Gate spec (finding #1), which makes the wrong dimensions and thresholds available to anyone reading the arch docs for decision-making. The highest-impact code change is fixing config.yaml's test zone auto_approve (finding #5/#10), which currently disagrees with both yolo_config.yaml and the runtime code.
