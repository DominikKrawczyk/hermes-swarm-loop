# LOOP 2 Phase 2 Point 1 — Config & Test Audit Report

## Date: 2026-06-02
## Repository: /root/code/hermes-swarm-loop
## HEAD: 4758784acd3a86b90bdfc904cb597cb496f7b46f

---

## PART 1: CONFIGS AUDIT

### 1.1 Config Files Present

| File | Status |
|------|--------|
| configs/config.yaml | ✓ Active |
| configs/yolo_config.yaml | ✓ Active |
| configs/scaling_config.yaml | ✓ Active |
| configs/__init__.py | ✓ Package marker |
| config.yaml (root) | ✓ Root-level config |
| configs/logging_config.yaml | ✗ MISSING (referenced!) |

### 1.2 configs/config.yaml — Checks

- **Version**: `6.5.1` — Present and reasonable
- **YOLO auto_approve**: safe=false, test=false, staging=true, production=true — ✓ Matches engine constants
- **Phase structure**: 5 phases, 3 points each, agents_per_point correctly set — ✓
- **Mastery gate weights sum to 1.0**: correctness=0.25 + safety=0.20 + test_coverage=0.15 + consistency=0.15 + diversity=0.10 + efficiency=0.10 + clarity=0.05 = 1.0 — ✓
- **Mastery gate thresholds**: pass=0.70, cross_check=0.50, review=0.30 — ✓

### 1.3 configs/yolo_config.yaml — Checks

- auto_approve settings match config.yaml and engine YOLO_ZONES — ✓
- Zone limits: safe=5, test=11, staging=33, production=999 — ✓
- Safety valve config present with thresholds — ✓
- default_zone: test — ✓
- Extra: subagent_inheritance, escalation_chain — Not in engine defaults but valid runtime config

### 1.4 configs/scaling_config.yaml — DRIFT FOUND

Comparison with `engine/config.py` DEFAULT_SCALING_CONFIG:

| Key | Config File | Engine Default | Match |
|-----|-------------|----------------|-------|
| token_bucket.rate | 10 | 10.0 | ✓ |
| token_bucket.burst | 20 | 50 | ✗ DRIFT |
| adaptive_batcher.min_batch/min_batch_size | min_batch=3 | min_batch_size=5 | ✗ KEY NAME DRIFT |
| adaptive_batcher.max_batch/max_batch_size | max_batch=100 | max_batch_size=50 | ✗ KEY NAME DRIFT |
| circuit_breaker.failure_threshold | 5 | 5 | ✓ |
| circuit_breaker.recovery_timeout/recovery_timeout_s | 30 | 30 | ✓ (key name variant) |
| circuit_breaker.half_open_max_requests | 3 | 3 | ✓ |
| connection_pool.max_connections | 10 | 20 | ✗ DIFFERENT VALUE |
| connection_pool.min_connections | not present | 2 | ✗ MISSING KEY |
| priority_queue | tiers dict | max_size=1000, default_priority=5 | ✗ COMPLETELY DIFFERENT |
| queue_pressure | max_depth, throttle_threshold, check_interval | high_watermark=0.8, low_watermark=0.3 | ✗ DIFFERENT STRUCTURE |

**Impact**: `_deep_merge` will produce a config with BOTH sets of keys at nested levels. The engine code reads `min_batch_size`, but the YAML only sets `min_batch`. The code default of 5 will be used silently instead of 3. The priority_queue and queue_pressure sections are completely different structures.

### 1.5 Root config.yaml Issues

- **MISSING FILE**: `configs/logging_config.yaml` is referenced in `config_paths.logging` but does not exist
- **Version drift**: root config.yaml = "0.1.0", configs/config.yaml = "6.5.1"

### 1.6 Loop 1 Fixes Verification

| Fix Required | Status | Evidence |
|-------------|--------|----------|
| safety valve restore | ✓ FIXED | reset_safety_valve() present in YOLOMachine |
| timeout race | ✓ FIXED | CAS version-checking in all DB writes |
| empty-list guard | ✓ FIXED | mastery_gate.evaluate raises ValueError on empty |
| repr lock | ✓ FIXED | Dataclass repr works for all state types |
| config.yaml auto_approve | ✓ CORRECT | Matches engine YOLO_ZONES |
| Version field present | ✓ PRESENT | "6.5.1" in configs/config.yaml |

---

## PART 2: TESTS AUDIT

### 2.1 Test Files Found

10 test files + conftest.py + __init__.py:

1. test_config.py — 10 test classes, ~215 lines
2. test_state_machine.py — 10 test classes, ~815 lines
3. test_scaling.py — Multiple classes, ~845 lines
4. test_mastery_gate.py — 5 test classes, ~178 lines
5. test_gate_11.py — 5 test classes, ~259 lines
6. test_integration.py — 6+ test classes, ~658 lines
7. test_bootstrap.py — 7+ test classes, ~372 lines
8. test_agent_roles.py — 1 class, ~99 lines
9. test_workspace_manager.py — 6+ test classes, ~384 lines
10. test_synthesizer.py — 3 classes, ~157 lines
11. tests/conftest.py — Fixtures
12. tests/__init__.py — Package marker

### 2.2 Test Count (estimated from git log)

Previous runs: 376–390 tests collected across all test files.

### 2.3 Collection Issues

**No tests appear intentionally excluded.** All files follow pytest conventions (class-based, test_ prefix). The `test_workspace_manager.py` module imports Gate11Verifier at the top (unused in workspace tests but present for smoke tests at bottom).

### 2.4 Import Issues — Scaling Tests

**test_scaling.py** imports from the `scaling/` package (e.g., `from scaling.token_bucket import TokenBucket`). Unlike all other 9 test files, it does NOT include:

```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
```

This means:
- Works fine when pytest is run from `/root/code/hermes-swarm-loop/` (project root)
- **FAILS** with ImportError when run from any other directory
- All other test files have the sys.path fix and are location-agnostic

### 2.5 Flaky Test Assessment

Identified potential flaky tests:

1. **test_scaling.py**: `TestCircuitBreaker.test_half_open_after_timeout` — uses `time.sleep(0.06)` for timing. On a loaded system, 60ms may not be enough.
2. **test_scaling.py**: `TestCircuitBreaker.test_half_open_success_closes` — same pattern with 0.06s sleep.
3. **test_workspace_manager.py**: Worktree tests use `subprocess.run` for git operations — could be flaky if git is slow.
4. No other obvious timing-dependent tests.

### 2.6 NOTE: Test Execution Not Possible

Due to a terminal environment issue (deleted process CWD), the test suite could not be executed. Analysis is based on static code inspection of all test files and the git log which reports 376/390 tests passing from prior runs.

---

## PART 3: FILE CHANGE AUDIT

### 3.1 Git History

All 6 commits in the repository from 2026-06-02:
1. Clone from origin/main
2. "Phase 2 Point 1: Code audit complete — 390/390 tests pass"
3. "Phase 2 Point 1: Code audit Agent 11 — 4 bugs fixed"
4. "Phase 2 Point 2: Code Improve Agent 11 — 3 findings fixed, 376/376 tests pass"
5. "Phase 2 Point 3: Code Review Agent 06 — review report"
6. "Agent 09: Supplementary code review — all 8 bugs verified fixed, 376/376 tests pass, APPROVE"

**No new files or commits since the previous audit.** HEAD is at commit 4758784 (final approval commit).

### 3.2 Untracked Files

Could not be checked due to terminal tool unavailability.

---

## FINDINGS SUMMARY

### Bugs
1. **Missing `configs/logging_config.yaml`** (HIGH) — Referenced but absent.

### Config Drift
2. **scaling_config.yaml ↔ engine constants drift** (MEDIUM) — Multiple key name mismatches and structural differences.

### Test Issues
3. **test_scaling.py lacks sys.path fix** (MEDIUM) — Unlike all other test files, not portable.

### Minor
4. **Version drift** (LOW) — root config.yaml vs configs/config.yaml versions differ.
5. **token_bucket burst mismatch** (LOW) — config=20, engine default=50.

### Verified Fixed from Loop 1
All 6 known fixes confirmed applied and correct. ✓
