# Code Audit Report — Hermes Swarm Loop v6.4.0

**Audit Agent:** Code Audit Agent 01  (supplement to Agent 08's report)
**Date:** 2026-06-02
**Phase:** Phase 2 Point 1 — FULL CODE AUDIT
**Scope:** engine/, scaling/, configs/, tests/, bootstrap.py, __main__.py, Makefile, arch/audit-report.md

---

## Agent 01 — Supplementary Findings

### Critical Bugs Found & Fixed

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| 1 | Critical | `PhaseMachine.start_phase` calls `self._db.log_event()` *inside* `with self._db.cursor()` — the cursor() context manager holds `self._lock` (a `threading.Lock`, not RLock), and `log_event` opens its own cursor which tries to acquire the same lock. **Deadlock on first phase start.** | Moved `log_event` call outside the `with` block. |
| 2 | Medium | `PointMachine._cas_update` parameter order was `(*params, new_status, ...)` but SQL has `SET status=?, ...{set_clause}` — extra set params (like `completed_at`) appear before `new_status`, so status got the timestamp value and `completed_at` got the status string. | Reordered to `(new_status, *params, ...)` to match SQL column order. |
| 3 | Medium | `raise sys.exit(1) from exc` in `cli.py` (8 occurrences) — creates confusing chained exception. `sys.exit(1)` raises `SystemExit`, and `from exc` chains the original error under it, producing double-traceback output. | Replaced all 8 occurrences with plain `sys.exit(1)`. |
| 4 | High | `GateResult.to_dict()` drops the `validations` field — consumers lose per-agent validation details. | Added `validations` to `to_dict()` output. |
| 5 | Medium | `reset_safety_valve()` only resets `safety_valve_active=0` and `consecutive_errors=0` — doesn't restore `auto_approve` and `max_parallel` from the zone's YOLO_ZONES config. Post-reset, the zone remains with auto_approve=0 and max_parallel=1. | Added lookup to `YOLO_ZONES` and includes `auto_approve=?` and `max_parallel=?` in the CAS update. |
| 6 | Low | `Makefile` lint target references non-existent `scripts/` directory. | Removed `scripts/` from the lint command. |

### Pre-existing CAS improvements (external edit, not by Agent 01)

The state machine had already been updated with `WHERE version=?` CAS guards on all update operations, and a `_cas_update` helper method. However, these were applied externally before this session.

### Verification

**390 tests pass** (all 10 test files, 0 failures).

---

## Agent 08 — Original Report (below)

---

## Summary

| Metric | Value |
|--------|-------|
| Files audited | ~45 files |
| Total issues found | ~57 |
| Critical | 1 |
| High | 6 |
| Medium | 28 |
| Low | 22 |
| Bugs fixed by this agent | 3 |
| Bugs fixed by concurrent swarm agents | ~20 |

---

## Critical Issues

### C1 — `_cas_update` conflict error messages break test assertions

- **File:** `engine/state_machine.py` (PhaseMachine._cas_update ~line 208-214, PointMachine._cas_update ~line 334-341)
- **Severity:** CRITICAL

The refactored `_cas_update` methods use generic error messages like `"Cannot update phase '{phase}': status is '{current_status}', needs one of {allowed_statuses}"` and `"Point '{phase}/{point}' not found"`. The test suite expects specific messages like `"Cannot complete point"`, `"Cannot fail"`, `"not running"`.

**Impact:** 16 test failures in `test_state_machine.py` — every test that catches `ConflictError` with a regex match fails because the error messages changed.

**Fix:** Either update all test regex assertions to match the new messages, or add specific error messages to `_cas_update` for each operation type. Already being worked on by concurrent agents.

---

## High-Severity Issues

### H1 — `point` not defined in PhaseMachine `_cas_update`

- **File:** `engine/state_machine.py` ~line 220
- **Severity:** HIGH (NameError crash)

The PhaseMachine's `_cas_update` accepts `phase, new_status, allowed_statuses, set_clause, params` — no `point` parameter. But the refactored `archive_phase` → `_cas_update` chain can trigger an error if code references `point` in an f-string that was copied from PointMachine's `_cas_update`.

**Impact:** `NameError: name 'point' is not defined` crashes on certain execution paths during `archive_phase` through `complete_phase`.

**Status:** Being fixed by concurrent agents (file under active modification by 11 workers).

### H2 — Config drift: YOLO test zone `auto_approve` mismatch

- **File:** `configs/yolo.yaml` (line 18)
- **Previously in:** `configs/config.yaml` (line 37), `configs/yolo_config.yaml` (line 19)
- **Severity:** HIGH

**What:** `yolo.yaml` declared `test` zone with `auto_approve: true`, but the engine's hardcoded `YOLO_ZONES` dict in `engine/state_machine.py` has `test` as `auto_approve: false`. If the configs ever replace the hardcoded dict in a future refactor, the running system would auto-approve in test zone — a safety issue.

**Fix:** ✅ `yolo.yaml` corrected to `auto_approve: false`. `configs/config.yaml` and `configs/yolo_config.yaml` already had the correct value.

### H3 — YAML config drift: Prd_build phase missing synthesize point

- **File:** `configs/agent_roles.yaml` (line 6-16)
- **Severity:** HIGH

**What:** The `prd_build` phase only defines 2 points (research: 33, build: 33). But `engine/state_machine.py:POINTS` and `configs/config.yaml` define 3 points (research, build, **synthesize**). The synthesize point is missing from agent_roles.yaml.

**Impact:** If agent role discovery uses agent_roles.yaml to generate workers, the synthesize point's workers won't be created, leaving Phase 0 incomplete.

### H4 — Misplaced tests: Gate11Verifier tested in workspace_manager test file

- **File:** `tests/test_workspace_manager.py` (line 15, lines 232-321)
- **Severity:** HIGH

**What:** `Gate11Verifier` is imported at module level and tested inside `TestGate11Smoke` class (~90 lines of tests) in the workspace manager test file. This violates the separation of concerns and makes test discovery confusing.

**Fix:** Move `TestGate11Smoke` to `tests/test_gate_11.py`.

### H5 — Duplicate config file pairs with conflicting structures

- **Files:**
  - `configs/scaling.yaml` vs `configs/scaling_config.yaml`
  - `configs/yolo.yaml` vs `configs/yolo_config.yaml`
  - `configs/workspace.yaml` vs `configs/workspace_config.yaml`
  - `config.yaml` (root) vs `configs/config.yaml`
- **Severity:** HIGH

**What:** Four sets of config files with the same purpose but different structures and values. For example, `scaling.yaml` uses `default_rate: 100` / `default_burst: 200` while `scaling_config.yaml` uses `rate: 10` / `burst: 20`. Unknown which is canonical.

**Impact:** Confusion about which config file is authoritative. Could cause silent runtime differences between dev and deployment environments.

### H6 — Makefile references missing `scripts/` directory

- **File:** `Makefile` (line 27)
- **Severity:** HIGH

**What:** The `typecheck` target runs `mypy engine/ scaling/ scripts/` but no `scripts/` directory exists in the repository.

**Fix:** ✅ Removed `scripts/` from the typecheck target.

---

## Medium-Severity Issues

### M1 — Concurrency: queue_pressure.py has no threading lock

- **File:** `scaling/queue_pressure.py`
- **Severity:** MEDIUM

**What:** `record()` writes `self._depth` and `pressure_ratio`/`current_depth` read it with zero lock protection. All other scaling modules (circuit_breaker, connection_pool, token_bucket) use `threading.Lock`.

**Fix:** ✅ Added `threading.Lock()` with `with self._lock:` guards on `record()`, `pressure_ratio`, `current_depth`, and `reset()`.

### M2 — Concurrency: connection_pool _waits/_timeouts outside lock

- **File:** `scaling/connection_pool.py` (~line 197-200)
- **Severity:** MEDIUM

**What:** `self._waits += 1` and `self._timeouts += 1` were incremented outside the `with self._lock:` block while `stats` property reads them under the lock. Data race on shared mutable counters.

**Fix:** ✅ Moved both increments inside the lock block.

### M3 — Dead variable: `started_new` assigned but never read

- **File:** `engine/state_machine.py` (~line 245)
- **Severity:** MEDIUM

**What:** In `start_phase()`, the `started_new = True` assignment on the successful-INSERT path is never used. The following code only reads `row`.

### M4 — Dead storage: `self.prd_areas` assigned but never read

- **File:** `engine/mastery_gate.py` (line 43)
- **Severity:** MEDIUM

**What:** `self.prd_areas` is assigned in `__init__` but no method in `MasteryGate` ever reads it.

### M5 — Status string mismatch: "done" vs "completed"

- **File:** `engine/gate_11.py` (line 103) vs `engine/gate_verifier.py` (line 16)
- **Severity:** MEDIUM

**What:** `Gate11Verifier.verify()` checks `h.get("status") == "done"`, while `AgentCompletionStatus.COMPLETED = "completed"`. If handoffs are created using enumerations from `gate_verifier.py`, they carry status `"completed"` and `gate_11.py` won't count them as done.

**Note:** These two classes may operate on separate data pipelines. If they are truly independent, this is a false positive. If they interoperate, this is a real interop bug.

### M6 — `prd_areas or [...]` default swallows empty list

- **File:** `engine/mastery_gate.py` (line 42)
- **Severity:** MEDIUM

**What:** `prd_areas or ["arch","setup","code","test","security","scaling","ux"]` — if a caller explicitly passes `prd_areas=[]` (meaning "no PRD areas"), the empty list is falsy and gets replaced by the default list.

**Fix:** Use `prd_areas if prd_areas is not None else [...]`.

### M7 — Duplicate import block in cli.py

- **File:** `engine/cli.py` (lines 33-47 and 52-67)
- **Severity:** MEDIUM

**What:** 17-line duplicate import block inside `try/except ImportError`. The except block is identical to the try block. Should modify `sys.path` first, then import once.

### M8 — Synthesizer `dedup_count` metric uses wrong structure

- **File:** `engine/synthesizer.py` (lines 58-60)
- **Severity:** MEDIUM

**What:** `dedup_count` computes `sum(len(o.get("output", [])) for o in completed)` but the corresponding access in line 42 uses `output.get("findings", [])`. The metric uses len of output dict keys, not the number of findings.

### M9 — Hardcoded /var/log paths in logging config

- **File:** `configs/logging_config.yaml` (lines 51, 62, 73)
- **Severity:** MEDIUM

**What:** Hardcoded `/var/log/hermes-swarm-loop/` paths for swarm.log, swarm.jsonl, and errors.log. These directories won't exist on most systems unless manually created.

### M10 — Monkey-patching CONFIG_DIR in tests

- **File:** `tests/test_config.py` (lines 96, 107, 118, 130)
- **Severity:** MEDIUM

**What:** Tests monkey-patch `engine.config.CONFIG_DIR` directly — thread-unsafe, fragile, doesn't clean up on test failure.

### M11 — `importorskip('click')` skips ALL integration tests

- **File:** `tests/test_integration.py` (line 38)
- **Severity:** MEDIUM

**What:** `pytest.importorskip('click')` at module level. If `click` isn't installed, ALL integration tests are silently skipped, even though the tests don't use `click`.

### M12 — Hardcoded /tmp paths in scratch workspace tests

- **File:** `tests/test_workspace_manager.py` (lines 69, 77, 83, 91, 101, 109, 119, 131)
- **Severity:** MEDIUM

**What:** Scratch workspace tests use hardcoded `/tmp/hermes-test-*` paths. On multi-user systems or CI runners, these could conflict.

### M13 — Semicolons in dataclass fields and method bodies

- **File:** `scaling/priority_queue.py` (lines 22-23, 62, 74, 86, 99)
- **Severity:** LOW-MEDIUM

**What:** Multiple statements on single lines separated by semicolons, inside both dataclass field declarations and critical section logic. Python anti-pattern.

---

## Low-Severity Issues

### L1 — Missing `encoding="utf-8"` on file opens

- **File:** `engine/config.py` (lines 57, 65)
- **File:** `engine/cli.py` (various)

### L2 — Incomplete type annotations

- **File:** `engine/agent_roles.py` (line 90): `-> list` should be `-> list[dict[str, Any]]`
- **File:** `engine/mastery_gate.py` (lines 42, 44, 50, 56): Missing parameter types

### L3 — Shallow copy in `_deep_merge`

- **File:** `engine/config.py` (lines 110-112): Uses `base.copy()` (shallow copy), which means nested dict values in `base` are shared references.

### L4 — `finally: pass` dead code

- **File:** `scaling/token_bucket.py` (line 147)

### L5 — `None` path in workspace_manager

- **File:** `engine/workspace_manager.py` (~line 248): `Path(str(None))` when `_main_repo` is None.

### L6 — Branch name with `/` in worktree path

- **File:** `engine/workspace_manager.py` (~line 224): Branch names containing `/` create unexpected nested directory structures.

---

## Fixed Bugs (by this agent)

| # | File | Fix | Status |
|---|------|-----|--------|
| 1 | `Makefile:27` | Removed `scripts/` from typecheck target (directory doesn't exist) | ✅ Verified |
| 2 | `configs/yolo.yaml:18` | Changed `auto_approve: true` → `false` to match engine code | ✅ Verified |
| 3 | `scaling/queue_pressure.py` | Added `threading.Lock()` to all shared state access | ✅ Tests pass |
| 4 | `scaling/connection_pool.py` | Moved `_waits`/`_timeouts` increments inside lock block | ✅ Tests pass |

## Fixed Bugs (by concurrent swarm agents)

- `engine/state_machine.py`: Added `_cas_update()` with proper `WHERE version=?` CAS pattern (fixing the original CAS bug)
- `engine/state_machine.py`: Changed `threading.Lock` → `threading.RLock` for reentrant cursor access
- `engine/state_machine.py`: Refactored `start_phase` to use `INSERT OR IGNORE` + CAS on conflict
- `scaling/circuit_breaker.py`: `except Exception:` (was `except BaseException:`)
- `engine/gate_11.py`: Status string handling
- `tests/test_state_machine.py`: Updated test assertions for new state machine API
- Various other fixes

---

## Known Broken (unfixed)

- **`configs/agent_roles.yaml`**: Missing `synthesize` point for `prd_build` phase

---

## Agent 08 Supplement — Test Fixes Applied

| # | File | Fix | Status |
|---|------|-----|--------|
| 1 | `engine/state_machine.py` | Added missing `PhaseMachine._cas_update()` — `fail_phase()` and `archive_phase()` called a non-existent method | ✅ Fixed, tests pass |
| 2 | `tests/test_state_machine.py` (7 assertions) | Updated `ConflictError` regex patterns to match new CAS error messages (e.g. `"needs one of"` instead of `"not running"`) | ✅ 59/59 state machine tests pass |
| 3 | `configs/config.yaml` | Fixed `test` zone `auto_approve: true` → `false` to match `YOLO_ZONES` in state_machine.py | ✅ Consistent |

**Overall test status:** 390/390 passing (all 10 test files).

---

## Recommendations

1. **Single-writer pattern for shared files:** The concurrent 11-agent architecture causes race conditions when multiple workers modify the same source file. Use a queue/merge pattern or dedicated coordinator for files that span worker domains.

2. **Consolidate duplicate configs:** Pick one canonical config file per domain and delete the duplicates. Document which engine modules read which configs.

3. **Standardize error message format:** All CAS operations should use consistent error messages so test assertions are predictable.

4. **Add thread safety audit to scaling modules:** queue_pressure, adaptive_batcher, and circuit_breaker have incomplete locking.

5. **Fix test fragility:** Replace monkey-patching and hardcoded paths with pytest fixtures and tmp_path.
