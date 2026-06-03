# Phase 3 Point 1: Bug Hunting Report — Agent 06

**Bug Hunter:** Agent 06 (`t_cd8957df`)
**Date:** 2026-06-02
**Codebase:** Hermes Swarm Loop v6.5.x
**Tests:** 376/376 passing after all fixes

---

## Summary

6 bugs found: 1 CRITICAL (crash), 2 HIGH (logic/concurrency), 2 MEDIUM, 1 LOW.
All bugs fixed and verified. Test suite passes at 100%.

---

## Bug 1 (CRITICAL): `start_phase` crashes on `sqlite3.Row.get()`

**File:** `engine/state_machine.py:196`
**Status:** ✅ FIXED

**Issue:** `start_phase()` calls `existing.get("status")` on a `sqlite3.Row` object, but `sqlite3.Row` does not have a `.get()` method — it supports dictionary-style access via `row["column"]` but not `.get()`. Additionally, the SELECT only fetched `version`, not `status`, so even if `.get()` existed, it would return None.

**Trigger condition:** Calling `start_phase()` on an existing phase (done, failed, or archived) raises `AttributeError: 'sqlite3.Row' object has no attribute 'get'`.

```python
# CRASH — before fix
c.execute("SELECT version FROM phase_state WHERE phase=?", (phase,))
existing = c.fetchone()
if existing is not None:
    if existing.get("status") == "done":  # AttributeError!
```

**Fix:** Changed SELECT to fetch `version, status`, and use `existing["status"]` (dict-style access) instead of `existing.get("status")`.

---

## Bug 2 (HIGH): `start_phase` COALESCE chain can't set 'archived' or 'todo' to 'running'

**File:** `engine/state_machine.py:202`
**Status:** ✅ FIXED

**Issue:** The UPDATE used `COALESCE(NULLIF(NULLIF(status, 'done'), 'failed'), 'running')` to try setting status to 'running'. This only works for 'done' and 'failed' statuses. For 'archived' and 'todo' statuses, the value remains unchanged — 'archived' stays 'archived', 'todo' stays 'todo' instead of becoming 'running'.

**Fix:** Replaced the complex COALESCE chain with a direct `SET status='running'`, combined with a pre-update check that rejects 'done' and 'archived' phases with a `ConflictError`. Failed phases are allowed to restart (they were already handled by the COALESCE chain).

---

## Bug 3 (HIGH): `CircuitBreaker.record_success()` doesn't auto-transition from OPEN

**File:** `scaling/circuit_breaker.py:112`
**Status:** ✅ FIXED

**Issue:** When the circuit is OPEN and the recovery timeout has elapsed, `record_success()` would early-return with `if self._state == CircuitState.OPEN: return` without checking the timeout. The `state` property and `allows_request()` both call `_check_timeout()` to auto-transition OPEN→HALF_OPEN, but `record_success()` and `record_failure()` did not.

**Consequence:** After a timeout recovery, the first successful call was silently ignored. The circuit stayed OPEN until someone read `allows_request()` or `.state`, which would trigger the transition.

```python
# Before fix — no timeout check before the OPEN guard
def record_success(self):
    with self._lock:
        if self._state == CircuitState.OPEN:
            return  # Silent no-op even after timeout elapsed
```

**Fix:** Added `self._check_timeout()` at the top of `record_success()`, matching the pattern already used in `.state` and `allows_request()`.

---

## Bug 4 (MEDIUM): `Gate11Verifier.all_done` doesn't verify ALL handoffs are done

**File:** `engine/gate_11.py:110`
**Status:** ✅ FIXED

**Issue:** `result.all_done` was set to `completed >= self.REQUIRED_COUNT`. If the verifier received 13 handoffs (e.g., due to retries), and 11 of them had status='done' but 2 were still running, `all_done` would be `True` (11 >= 11) even though 2 handoffs hadn't completed. This would cause the synthesizer to merge incomplete results.

**Fix:** Changed to `completed >= len(handoffs) and completed >= self.REQUIRED_COUNT`, ensuring all submitted handoffs are done before declaring the gate complete.

---

## Bug 5 (MEDIUM): `MasteryGate.check_diversification` only checks 3 of 7 dimensions

**File:** `engine/mastery_gate.py:72`
**Status:** ✅ FIXED

**Issue:** The `check_diversification()` method only checked `diversity`, `correctness`, and `safety` against the threshold. The other 4 dimensions (`test_coverage`, `consistency`, `efficiency`, `clarity`) could be arbitrarily low without being flagged as gaps.

```python
# Before fix — only 3 dimensions checked
if s.diversity < t: g.append(...)
if s.correctness < t: g.append(...)
if s.safety < t: g.append(...)
# test_coverage, consistency, efficiency, clarity — NOT checked
```

**Fix:** Replaced the hardcoded 3 checks with a loop over `DIMENSIONS`, checking all 7 dimensions against the threshold.

---

## Bug 6 (LOW): TOCTOU race in `increment_errors` → `activate_safety_valve`

**File:** `engine/state_machine.py:465`
**Status:** ✅ FIXED

**Issue:** `increment_errors()` incremented the error counter in one database transaction, then (if the threshold was met) called `self.activate_safety_valve()` in a **separate** transaction. Between the two transactions, another concurrent writer could increment errors again, causing the `activate_safety_valve()` call to fail with a CAS `ConflictError`, preventing the safety valve from activating even though the error threshold was exceeded.

**Fix:** Moved the safety valve activation inside the same cursor context as the error increment, so both operations are in a single atomic transaction.

---

## Concurrent-Agent Fixes (Discovered During Bug Hunting)

**Other agents in this swarm also fixed:**
1. **`engine/state_machine.py`** — Added `dict_handoffs` guard to filter non-dict handoffs (handles `AttributeError` on malformed handoff data)
2. **`scaling/circuit_breaker.py`** — Added `_half_open_in_flight` and `_half_open_max_probes` half-open throttling to limit probes
3. **`scaling/circuit_breaker.py:allows_request()`** — Added HALF_OPEN capacity check to prevent probe flooding

---

## Bug Report Summary

| # | Severity | File | Bug | Fixed |
|---|----------|------|-----|-------|
| 1 | CRITICAL | `engine/state_machine.py:196` | `sqlite3.Row.get()` crash in `start_phase()` | ✅ |
| 2 | HIGH | `engine/state_machine.py:202` | COALESCE can't set 'archived'/'todo' to 'running' | ✅ |
| 3 | HIGH | `scaling/circuit_breaker.py:112` | `record_success()` ignores timeout transition | ✅ |
| 4 | MEDIUM | `engine/gate_11.py:110` | `all_done` doesn't require ALL handoffs done | ✅ |
| 5 | MEDIUM | `engine/mastery_gate.py:72` | Only 3/7 dimensions checked for gaps | ✅ |
| 6 | LOW | `engine/state_machine.py:465` | TOCTOU in `increment_errors` → safety valve | ✅ |

**Final test suite:** 376/376 passed ✅
