# Phase 3 Point 1: Bug Hunting — Agent 01 Report

**Bug Hunter:** Agent 01 (`t_5947fde9`)
**Date:** 2026-06-02
**Codebase:** Hermes Swarm Loop v6.5.1
**Files audited:** All 34 source files (engine/*.py, scaling/*.py, tests/*.py, bootstrap.py, __main__.py, configs/*.py)

---

## Summary

- **3 bugs fixed** (1 LOW, 2 ADVISORY)
- **376/376 tests pass** (0 regressions)

Previous agents (03, 06, 08, 09) found & fixed 15+ bugs covering deadlocks, race conditions, logic errors, and thread safety. This sweep focused on remaining edge cases, inconsistent error handling, and code quality issues.

---

## Bug 1 (LOW): `load_yaml()` missing exception handling — inconsistent with `load_json()`

**File:** `engine/config.py:50-55`

**Severity:** LOW — crashes with malformed config files instead of gracefully returning `None`

**Root Cause:** `load_yaml()` does not catch `yaml.YAMLError` or other exceptions during file parsing. If a config file exists but contains malformed YAML (e.g., a syntax error or type that `yaml.safe_load` can't handle), the exception propagates up unhandled. Compare with `load_json()` which properly catches `json.JSONDecodeError` and `OSError` and returns `None`. Additionally, `load_yaml()` didn't validate that the loaded value is a `dict` — `yaml.safe_load` can return lists, scalars, or `None`, which would crash downstream code that expects a dict.

**Trigger:** A user has a `scaling_config.yaml` or `yolo_config.yaml` with a YAML syntax error, or containing a top-level list/scalar instead of a dict. `load_scaling_config()` or `load_yolo_config()` crashes with an unhandled exception instead of falling back to defaults.

**Fix:** Wrapped the file open + `safe_load` in a `try/except Exception` block, and added `isinstance(loaded, dict)` validation. Now returns `None` on any parsing failure, matching the behavior of `load_json()`.

### Before (broken)
```python
def load_yaml(path):
    if not path.exists():
        return None
    if not _HAS_YAML:
        return None
    with open(path) as f:
        return _yaml.safe_load(f)  # ← YAMLError propagates, non-dict types returned
```

### After (fixed)
```python
def load_yaml(path):
    ...
    try:
        with open(path) as f:
            loaded = _yaml.safe_load(f)
        if not isinstance(loaded, dict):
            return None
        return loaded
    except Exception:
        return None
```

---

## Bug 2 (ADVISORY): F-strings without placeholders

**Files:** `bootstrap.py:58`, `engine/cli.py:490,494`

**Severity:** ADVISORY — code style, not a runtime bug

**Issue:** Three f-strings are used without any interpolation expressions. While not a runtime error (Python still evaluates them correctly), they trigger `ruff F541` and waste a tiny amount of CPU creating `string.Formatter` objects for no benefit.

**Fix:** Removed the `f` prefix from these three strings.

### Before
```python
print(f"Hermes Swarm Loop — Bootstrap")
score_lines.append(f"\n[bold yellow]Gaps:[/bold yellow]")
score_lines.append(f"\n[green]No gaps detected.[/green]")
```

### After
```python
print("Hermes Swarm Loop — Bootstrap")
score_lines.append("\n[bold yellow]Gaps:[/bold yellow]")
score_lines.append("\n[green]No gaps detected.[/green]")
```

---

## Bug 3 (ADVISORY): `__all__` not sorted in `engine/__init__.py`

**File:** `engine/__init__.py:17-23`

**Severity:** ADVISORY — triggers `ruff RUF022`

**Issue:** The `__all__` list is not alphabetically sorted. Most tools expect sorted `__all__` for consistent import introspection. This triggers `ruff RUF022`.

**Fix:** Reordered `__all__` entries alphabetically.

### Before
```python
__all__ = [
    "StateDB", "PhaseMachine", "PointMachine", "YOLOMachine",
    "PhaseEntry", "PointEntry", "YOLOState", "ConflictError", "YOLO_ZONES",
    "MasteryGate", "ScoreCard", "score_from_dict", "DIMENSIONS",
    ...
]
```

### After
```python
__all__ = [
    "ConflictError", "DIMENSIONS", "Gate11Verifier",
    "GateResult", "HandoffValidation", "MasteryGate",
    ...
]
```

---

## Bugs Already Fixed by Concurrent Agents

| # | Severity | File | Issue | Agent |
|---|----------|------|-------|-------|
| 1 | CRITICAL | `state_machine.py:127` | Lock()→RLock() deadlock: log_event from inside cursor context | 09 |
| 2 | CRITICAL | `state_machine.py:193` | start_phase partial fix missing `status` column | 09 |
| 3 | CRITICAL | `state_machine.py:305` | create_point corrupted by parallel agent (NameError, wrong table) | 09 |
| 4 | HIGH | `state_machine.py:202` | COALESCE can't set 'archived'/'todo' to 'running' | 06 |
| 5 | HIGH | `circuit_breaker.py:112` | record_success() ignores timeout auto-transition | 06 |
| 6 | MEDIUM | `gate_11.py:110` | all_done doesn't require ALL handoffs done | 06 |
| 7 | MEDIUM | `mastery_gate.py:72` | Only 3/7 dimensions checked for diversification gaps | 06 |
| 8 | MEDIUM | `circuit_breaker.py:77` | state property race: _check_timeout() called without lock | 09 |
| 9 | MEDIUM | `connection_pool.py:209` | _waits inflated per loop iteration, not per acquire | 03 |
| 10 | LOW | `connection_pool.py:284` | _release() double-tracks connections | 09 |
| 11 | LOW | `connection_pool.py:203` | acquire() leaves _available_event set on timeout | 09 |
| 12 | LOW | `cli.py:88` | _load_project_config crashes on non-dict config | 09 |
| 13 | LOW | `bootstrap.py:90` | agent_count stores uncapped value despite YOLO zone | 09 |
| 14 | LOW | `state_machine.py:465` | TOCTOU between increment_errors and activate_safety_valve | 06 |
| 15 | LOW | `circuit_breaker.py:97` | HALF_OPEN allowed unlimited concurrent probes (from concurrent agent) | 03/06 |

---

## Audit Summary

| Metric | Value |
|--------|-------|
| Files audited | 34 source files (engine/ 9, scaling/ 8, tests/ 12, root 3, configs 2) |
| Lines of source code | ~8,500 (source) + ~9,500 (tests) = ~18,000 |
| Bugs found & fixed | 3 (1 LOW, 2 ADVISORY) |
| Previous bugs verified fixed | 15 (from agents 03, 06, 09) |
| Tests passed | 376/376 |
| Pass rate | 100% |
