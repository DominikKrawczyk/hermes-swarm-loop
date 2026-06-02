# Phase 3 Point 3: Synthesis Report — Hermes Swarm Loop

**Date:** 2026-06-02
**Synthesizer:** t_fe32dbd1 (default)
**Codebase:** Hermes Swarm Loop v6.5.1 at /opt/hermes-swarm-loop/

## Deliverables Confirmed

| Deliverable | Path | Status | Source |
|------------|------|--------|--------|
| Security Audit Report | arch/security-audit.md | Complete (541 lines, 17 findings) | Phase 3 Point 3 — 11 agents + verifier |
| Architecture Review Report | arch/architecture-review-report.md | Complete (338 lines, 13 inconsistencies + debt) | Phase 3 Point 2 |
| Code Audit Report | arch/audit-report.md | Complete (189 lines, 17 bugs fixed) | Phase 2 Point 1 |
| Bug Report | arch/bug-report.md | **NOT GENERATED** — findings consolidated into audit-report.md | Cross-referenced |
| Phase 2 Point 2 Summary | arch/phase2-point2-complete.md | Complete | Phase 2 Point 2 |

## Consolidated Findings Across All Reports

**Total unique findings: 47** (17 security + 13 arch inconsistencies + 17 code bugs)

### Cross-Cutting Themes

#### Theme 1: The COALESCE Bug (S1/B1) — The Most Rediscovered Bug in the Codebase

This single bug has been independently found by **every quality phase** since Phase 1, and **never fixed**:

| Phase | Report | Finding ID | Severity | Status |
|-------|--------|-----------|----------|--------|
| Phase 1 | Code generation | (implicit — bug was introduced) | — | Created |
| Phase 2 Point 1 | audit-report.md | (missed) | — | Not found |
| Phase 2 Point 2 | phase2-point2-complete.md | (missed) — CAS/config/synthesizer fixes only | — | Not found |
| Phase 3 Point 1 | Bug hunting (worker comments) | B1 | CRITICAL | Found, documented in skill, **not applied to repo** |
| Phase 3 Point 2 | architecture-review-report.md | (missed) — arch review doesn't dig into SQL semantics | — | Not found |
| Phase 3 Point 3 | security-audit.md | S1 | HIGH (7.0 CVSS) | **Still unfixed** |
| Phase 3 Point 3 | security-audit.md | S3 | MEDIUM (5.3 CVSS) | Process finding about repeated rediscovery |

**Why it keeps being rediscovered:** The bug is subtle — it compiles, does something (the wrong thing), and doesn't crash. The `COALESCE(NULLIF(status, 'done'), 'running')` pattern looks plausible on first read. An experienced reviewer catches it by asking "what happens if status is already 'failed'?" — which few reviewers think to ask when reviewing a "start phase" function.

**Fix:** Replace line 198 in engine/state_machine.py with explicit status guard:
```python
row = c.execute("SELECT status FROM phase_state WHERE phase=?", (phase,)).fetchone()
if row and row["status"] in ("done", "failed", "archived", "blocked"):
    raise ConflictError(f"Cannot start phase '{phase}': status is '{row['status']}'")
```

**Estimated effort:** 3 minutes. One-line edit, one test update.

---

#### Theme 2: Config Drift — Three Fixes Took Four Phases

Three config inconsistencies were independently flagged by multiple agents across phases and only resolved in Phase 3 Point 3:

| Issue | First Flagged | Fixed | Took |
|-------|--------------|-------|------|
| config.yaml test zone auto_approve=true (S2) | Phase 2 Point 1 (#4) | Phase 3 Point 3 | 3 phases |
| config.yaml version mismatch 6.4.0 vs 6.5.1 (S9) | Phase 2 (#14), Phase 3 Arch (#9) | Phase 3 Point 3 | 2-3 phases |
| Unused dependencies (S11) | Phase 2 (#3) | Phase 3 Point 3 | 2 phases |

These were straightforward fixes — each was a single line change. The delay was not technical but process: each phase assumes the previous phase already fixed the issues it flagged. The config files at /opt/ were not being updated by prior fix agents.

---

#### Theme 3: Scaling Modules — 1,340 Lines of Clean, Tested, Unused Code

All three reports independently note this:

| Report | Finding | Says |
|--------|---------|------|
| audit-report.md | Dead Code #2-#4 | CASEntry, ConflictError dead; scaling issues noted |
| architecture-review-report.md | #3 (HIGH), O1 | ALL 7 modules unwired — 1,340 lines |
| security-audit.md | S5, S17 | Only latent issue is PriorityQueue.size lock |

The modules are well-tested and architecturally clean — TokenBucket, AdaptiveBatcher, CASStore, CircuitBreaker, ConnectionPool, PriorityQueue, QueuePressure. Their only security impact is the PriorityQueue.size lock issue (S5, CVSS 4.0). The three reports agree: no action needed now, but the Simplicity phase should decide whether to wire them in or archive them.

---

#### Theme 4: Architecture Doc Drift — Documents Describe v6.4.0 Design Intent

The architecture documents were written at v6.4.0 as a pre-implementation blueprint. They've never been updated. The arch review report found 13 inconsistencies. The security audit confirmed the critical ones (config drift). The audit report found all 17 code bugs fixed but zero doc updates.

| Report | Verdict |
|--------|---------|
| architecture-review-report.md | "The most urgent fix is the Mastery Gate spec (finding #1)" |
| security-audit.md | "All 17 bugs are fixed in code. None are reflected in architecture documents." |
| audit-report.md | "390/390 tests passing — no regressions from any fix." |

---

#### Theme 5: Bug-Fixing Pipeline Leak

Multiple bugs found by Phase 3 Point 1 (bug hunting) were **never applied** to the code at /opt/:

| Bug | Found By | Severity | Filed in | Applied to /opt/? |
|-----|----------|----------|----------|-------------------|
| B1 — COALESCE (S1) | Bug hunting | CRITICAL | Skill update | **NO** |
| B4 — ConnectionPool lock (S2/others) | Bug hunting | MEDIUM | Bug report | **NO** |
| B5 — PriorityQueue size (S3/S5) | Bug hunting | MEDIUM | Bug report | **NO** |
| B6 — close_all leak | Bug hunting | MEDIUM | Bug report | **NO** |
| B10 — bootstrap cap bypass | Bug hunting | MEDIUM | Bug report | **NO** |

This is a pipeline leak: the bug hunting phase found the bugs and documented fixes, but the fixes were never applied to the literal files on disk at /opt/. Future phases need a validation step that checks "does the fix actually exist in the file?"

---

### Consolidated Remediation Priority List

Ranked by combined urgency across all three reports:

| Priority | ID(s) | What | Across Reports | Effort | Impact |
|----------|-------|------|---------------|--------|--------|
| **P0** | S1/B1 | Fix COALESCE bug in state_machine.py:198 | Security: HIGH (7.0), Bug hunt: CRITICAL, Arch: missed | 3 min | Prevents silent corruption of phase state |
| **P1** | S4 | Add branch name validation in workspace_manager.py:236 | Security: MEDIUM (5.5) | 15 min | Blocks git flag injection |
| **P2** | D2, #3 | Implement SQLite-backed CASStore or document in-memory limitation | Arch: MEDIUM-HIGH | 1-2h | Prevents state loss on restart |
| **P3** | S5 | Lock-protect PriorityQueue.size | Security: MEDIUM (4.0) | 2 min | Latent race condition |
| **P4** | #5 | Fix stale architecture docs (mastery-gate-spec.md, state-machine-architecture.md, yolo-zones.md) | Arch: 4 critical/medium findings | 1-2h | Prevents decision-making from wrong docs |
| **P5** | S6-S8, S12-S16 | Low-severity security fixes (CLI input validation, TOCTOU, permissions, deps pinning) | Security: LOW | 30 min | Defense in depth |
| **P6** | #1, D1 | Split state_machine.py into modular files | Arch: HIGH design debt | 2h | Long-term maintainability |
| **P7** | #3, O1, S17 | Wire or archive 1,340 lines of scaling modules | All three reports | 1h | Removes dead code confusion |
| **P8** | Various | Remaining arch doc updates and code quality issues | Arch: 9 additional findings | Varies | Documentation accuracy |

### Cross-Reference Verification

| Cross-Reference Requested | Status |
|---------------------------|--------|
| security-audit.md ↔ architecture-review-report.md | **Done** — 6 security-relevant arch inconsistencies cross-referenced in security audit |
| security-audit.md ↔ audit-report.md | **Done** — 5 key audit fixes cross-referenced for security relevance in security audit |
| security-audit.md ↔ bug-report.md | **Not applicable** — bug-report.md doesn't exist; findings in audit-report.md were used instead |
| architecture-review-report.md ↔ audit-report.md | **Done** — 7 audit bugs cross-referenced for architecture impact in arch review |

### Code Health Metrics (All Reports Agree)

| Metric | Value | Source |
|--------|-------|--------|
| Tests passing | 390/390 | audit-report.md, verified in arch review |
| Security profile | 0 critical, 1 high, 2 medium, 5 low | security-audit.md |
| Code bugs fixed | 17 | audit-report.md |
| Arch inconsistencies | 13 | architecture-review-report.md |
| Dead code lines | ~1,500 | Consensus (3 reports) |
| Scaling modules unwired | 7 modules, 1,340 lines | Consensus (3 reports) |

## Conclusion

The codebase is functionally solid (390/390 tests passing, 17 bugs fixed, 0 critical security vulnerabilities). The single most important unfixed issue is the COALESCE bug in start_phase (S1/B1) — a 3-minute fix that has been rediscovered across 4 quality phases without correction. The second most important issue is updating architecture documents that describe a v6.4.0 pre-implementation design rather than the actual v6.5.1 code.

The security posture is strong: no SQL injection, no command injection, no unsafe deserialization, no hardcoded secrets, and proper CAS locking across all 12 mutation methods. The security audit found 1 high-severity issue (the COALESCE bug, which is a logic flaw not an injection/secrets issue), 2 medium, and 5 low.

Key process improvement for future phases: after any bug-finding phase, add a verification step that checks whether the fix was actually applied to the files on disk — not just documented in a skill or comment.
