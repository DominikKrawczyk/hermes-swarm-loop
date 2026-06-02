# Code Audit Report — Agent 04

**Phase:** Phase 2 — Point 1: FULL CODE AUDIT
**Auditor:** Code Audit Agent 04
**Date:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")

Files audited: engine/*.py, scaling/*.py, configs/*.yaml, tests/*.py, bootstrap.py, __main__.py, Makefile, config.yaml

---

## ⚠ CRITICAL BUGS

### C01 — CAS Bug: Version columns incremented without `WHERE version=?` guard

**Files:** `engine/state_machine.py`
**Lines:** 220, 232, 248, 265, 306, 318, 335, 352, 401, 417, 428, 452
**Severity:** CRITICAL

**Description:** Every SQL UPDATE in the state machine increments `version=version+1`, but NONE of the UPDATE statements include a `WHERE version=?` clause. This defeats the entire purpose of optimistic CAS (compare-and-swap). Two concurrent workers can both read version 1, both perform an UPDATE, and both succeed — the version counter ticks but can't detect stale writes.

**Example** (line 232, `fail_phase`):
```sql
UPDATE phase_state SET status='failed', completed_at=?, version=version+1
WHERE phase=? AND status='running'
```
— should be:
```sql
UPDATE phase_state SET status='failed', completed_at=?, version=version+1
WHERE phase=? AND status='running' AND version=?
```

**Fix:** Add `AND version=?` to every UPDATE's WHERE clause. Pass the expected version as a parameter. Check `c.rowcount == 0` to detect conflicts and raise `ConflictError`.

**Evidence:** `grep -n "version=version+1" engine/state_machine.py` returns 12 lines, none with `WHERE.*version=?`. `grep -c "WHERE.*version" engine/state_machine.py` returns 0.

### C02 — DEFAULT_YOLO_CONFIG vs YOLO_ZONES inconsistency

**Files:** `engine/config.py` (line 42) vs `engine/state_machine.py` (line 387)
**Severity:** HIGH

**Description:** The DEFAULT_YOLO_CONFIG dict in config.py defines the "test" zone with `auto_approve: True`, but the actual YOLO_ZONES dict in state_machine.py (which is the runtime source of truth) defines "test" with `auto_approve: False`. Anyone loading the config via `load_yolo_config()` gets contradictory information.

```python
# config.py line 42:
"test": {"auto_approve": True, "max_parallel": 11}

# state_machine.py line 387:
"test": {"auto_approve": False, "max_parallel": 11, "max_errors": 5, "desc": "..."}
```

**Fix:** Make DEFAULT_YOLO_CONFIG match YOLO_ZONES. Set `"test": {"auto_approve": False, "max_parallel": 11}` in config.py.

### C03 — ConnectionPool race condition: _waits and _timeouts incremented outside lock

**File:** `scaling/connection_pool.py`, lines 197-198, 200
**Severity:** HIGH

**Description:** `self._waits += 1` (line 197) and `self._timeouts += 1` (line 200) are incremented OUTSIDE the `with self._lock:` block (lines 177-195). Under concurrent access, these increments can race and lose count.

```python
# At capacity — wait for a release
self._waits += 1              # ← OUTSIDE lock!
remaining = deadline - time.monotonic()
if remaining <= 0:
    self._timeouts += 1       # ← OUTSIDE lock!
```

**Fix:** Move the counter increments inside the `with self._lock:` block, or use `self._waits += 1` inside a locked scope before the wait.

---

## ⚡ MEDIUM ISSUES

### M01 — Dual gate verification systems (duplicate code)

**Files:** `engine/gate_11.py` (123 lines) vs `engine/gate_verifier.py` (118 lines)
**Severity:** MEDIUM

**Description:** Two completely separate gate verification systems:
- `Gate11Verifier` (`gate_11.py`): Hardcoded for 11-agent gate with `MINIMUM_HANDOFF_FIELDS`. Used by the CLI and the main orchestration workflow.
- `GateVerifier` (`gate_verifier.py`): Flexible JSON Schema-based validator with `HandoffSchema`. Exported via `engine/__init__.py` but NEVER used by any workflow code — only by its own test file `test_gate_verifier.py`.

~300 lines of dead/duplicate code. The `GateVerifier` has richer validation (type checking, enums, JSON Schema draft-2020-12) but is fully disconnected from the runtime.

**Evidence:** `grep -rn "GateVerifier" --include="*.py"` — only appears in `engine/__init__.py`, `engine/gate_verifier.py`, and `tests/test_gate_verifier.py`. Never imported by `cli.py`, `bootstrap.py`, or any workflow code.

### M02 — Synthesizer dedup_count crashes on non-list output

**File:** `engine/synthesizer.py`, line 58
**Severity:** MEDIUM

**Description:** The `dedup_count` calculation does `sum(len(o.get("output", [])) for o in completed)`. If any agent's output is a string or non-list type (e.g. `"output": "completed"`), `len()` raises `TypeError: object of type 'str' has no len()`. The merge logic on line 42 already handles this divergence, but the stats calculation doesn't.

```python
"dedup_count": sum(len(o.get("output", [])) for o in completed) - len(all_findings)
```

### M03 — Worktree setup doesn't create branch first

**File:** `engine/workspace_manager.py`, line 235
**Severity:** MEDIUM

**Description:** `_setup_worktree` runs `git worktree add <path> <branch>` but if the branch doesn't exist in the repository, git errors with "fatal: invalid reference". The branch needs to be created (e.g., `git branch <branch>`) before the worktree add.

**Evidence:** The test in `tests/test_workspace_manager.py` (line 348-351) manually runs `git branch feature/test-branch` before calling `setup("worktree")`, proving the workaround is known.

### M04 — Duplicate config files (6+ redundant files)

**Files under `configs/`:**
- `scaling.yaml` ↔ `scaling_config.yaml` (duplicates)
- `yolo.yaml` ↔ `yolo_config.yaml` (duplicates)
- `workspace.yaml` ↔ `workspace_config.yaml` (duplicates)
- `config.yaml` (configs/) + `config.yaml` (root) + `engine_config.yaml` (root-like but different schema)

**Severity:** MEDIUM

**Description:** 12 config files with multiple sets of duplicates. This creates confusion: which scaling.yaml is the canonical one? `load_config()` in `engine/config.py` only looks for `scaling_config.yaml`, yet `scaling.yaml` sits alongside it as a stale orphan.

---

## 🔧 LOW ISSUES

### L01 — CASStore (scaling/) disconnected from state_machine CAS

**File:** `scaling/cas_store.py`
**Severity:** LOW

**Description:** The scaling module has an in-memory CASStore with version-based CAS, but it's completely disconnected from `engine/state_machine.py`'s SQLite version-column pattern. They share the name "CAS" but do not interoperate. The scaling CASStore is never imported by any engine code.

### L02 — Dead code in gate_verifier.py: next_id autoincrement

**File:** `engine/gate_verifier.py`, lines 54, 60-61
**Severity:** LOW

**Description:** `_next_id` autoincrement generates monotonically increasing IDs for each validation result, but these IDs are never used for anything meaningful — not referenced by downstream consumers, not logged, not surfaced in any UI.

### L03 — Agent role domain diversity is limited

**File:** `engine/agent_roles.py`, lines 18-19
**Severity:** LOW

**Description:** `_domain_for(index)` rotates through only 33 DOMAINS for all 198 roles (66 for prd_build + 33×4 for the other phases). Many different roles share the same domain, reducing the diversity the PRD envisions.

### L04 — test_cursor_commit double-commits

**File:** `tests/test_state_machine.py`, lines 46-47
**Severity:** LOW

**Description:** `cur.connection.commit()` is called inside the `db.cursor()` context manager, which also auto-commits on exit (line 171 in state_machine.py). The write succeeds but this is a test smell that could mask bugs or produce confusing test failures.

---

## ✅ Fixes Applied

1. **C02** — Fixed `engine/config.py` DEFAULT_YOLO_CONFIG "test" zone auto_approve to match YOLO_ZONES (True → False). Verified: `load_yolo_config()` now returns auto_approve=False for test zone, consistent with the runtime YOLO_ZONES dict.

2. **C03** — Fixed `scaling/connection_pool.py`: moved `_waits` and `_timeouts` increments inside the lock scope, preventing race conditions on concurrent `acquire()` calls.

3. **M02** — Fixed `engine/synthesizer.py`: rewrote `dedup_count` calculation to be defensive against non-list output types (str, dict, None). No more `TypeError: object of type 'str' has no len()` when agents return non-standard output formats.

4. **L04** — Fixed `tests/test_state_machine.py` test_cursor_commit: removed redundant `cur.connection.commit()` call inside the cursor context manager (which already auto-commits on exit).

### Fix Verification
| Fix | Test Coverage | Status |
|-----|--------------|--------|
| C02 (config YOLO) | `test_config.py -k yolo` (4 tests) | ✅ PASS |
| C03 (connection pool lock) | `test_scaling.py -k ConnectionPool` (5 tests) | ✅ PASS |
| M02 (synthesizer) | `test_synthesizer.py` (20 tests) | ✅ PASS |
| L04 (test clean) | `test_state_machine.py -k cursor_commit` | ✅ PASS |

---

## Summary

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 3     |
| MEDIUM   | 4     |
| LOW      | 4     |
| **Total**| **11**|

4 bugs fixed in this run. 7 issues documented for follow-up.
