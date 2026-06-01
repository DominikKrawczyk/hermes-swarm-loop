---
name: hermes-swarm-loop
description: "3×3×3×N Hermes Swarm Loop — Development (AUDIT→IMPROVE→REVIEW) × Hunting (BUGS→ARCH→SECURITY) × Simplicity/Consolidation (REFACTOR→OCCAM→PRD-ALIGN) × N agents via hermes kanban swarm. Cross-model review. Self-reflection: masterpiece/flawed/cannot-improve. YOLO mode."
version: 4.0.0
author: Edward Puszczyk (github: DominikKrawczyk)
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [ralph-loop, swarm, multi-agent, kanban, deepseek, iteration, hunting, self-reflection, yolo, cross-model-review]
    related_skills: [claude-code, codex, hermes-agent, subagent-driven-development]
---

# Hermes Swarm Loop — 3×3×3×N

## When to Use

This skill defines the **3-Loop Hermes Ralph** — a prompt-based methodology for building anything with autonomous agent iteration, using the **native Hermes Kanban Swarm** API to spawn parallel agents.

Use when:
- Building **blockchain, huge infrastructure, complex applications** from scratch
- You want the agent to iterate in **3-point cycles × 3 loop types × 3 sub-iterations × N agents** until truly done
- You need **33→999 agents** working in parallel via `hermes kanban swarm`
- You want automatic **bug hunting, architecture review, security scanning, AND simplicity/consolidation audit**
- You need **cross-model review** to break self-play blind spots
- You need **self-reflection** to determine mastery vs flawed vs plateau

**Key insight:** This is a **prompt methodology** executed via `hermes kanban swarm` — NOT `delegate_task()`. The kanban swarm spawns N parallel workers, a verifier, and a synthesizer as native Hermes tasks. Each worker runs in an isolated workspace.

**Inspiration:** Ralph Loop (19.8k⭐) × Ralphy (2.9k⭐) × ARIS (11.2k⭐) × Hive (10.5k⭐)

---

## Core Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LOOP 1: DEVELOPMENT        LOOP 2: HUNTING         LOOP 3: SIMPLICITY      │
│  (AUDIT→IMPROVE→REVIEW)     (BUGS→ARCH→SECURITY)    & CONSOLIDATION         │
│  × 3 subs × N swarm each    × 3 depths × N swarm    × 3 points × N swarm    │
│                                                                             │
│  AUDIT ─┬─ Surface (N/3)    BUGS ─┬─ L1: Syntax     1. Dead Code            │
│          ├─ Deep (N/3)              ├─ L2: Runtime       Consolidate          │
│          └─ Exhaustive (N/3)        └─ L3: Heisen        (NOT destroy)       │
│                                                    2. Occam's Razor          │
│  IMPROVE ┬─ Critical (N/3)   ARCH ─┬─ L1: Structure                          │
│          ├─ Feature (N/3)           ├─ L2: Coupling    3. PRD ALIGNMENT      │
│          └─ Polish (N/3)            └─ L3: Scale        ← BACK TO LOOP 1     │
│                                                     (gap findings fed to     │
│  REVIEW ─┬─ Auto-verify      SEC ─┬─ L1: Secrets       next Loop 1)          │
│           ├─ Manual logic           ├─ L2: OWASP                             │
│           └─ Quality gate           └─ L3: Crypto                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
              Every 3 full cycles: SELF-REFLECTION JURY
              → MASTERPIECE (≥0.85, flaws<5, improving) → SHIP
              → FLAWED (any<0.7 or flaws>10) → LOOP AGAIN
              → CAN'T IMPROVE (3 cycles flat) → STOP
```

**Agent spawning:** All parallel agents are spawned via `hermes kanban swarm` — each worker in an isolated workspace. Gateway processes them asynchronously.

---

## Quick Start

```bash
# Get the framework
git clone https://github.com/DominikKrawczyk/hermes-swarm-loop.git
cd hermes-swarm-loop

# 1. Start the gateway (needed for kanban tasks to run)
hermes gateway start

# 2. Create a board for your project
hermes kanban boards create my-project

# 3. Run AUDIT phase with N agents
hermes kanban boards switch my-project
hermes kanban swarm \
  --worker default:"Surface audit pt1":hermes-swarm-loop \
  --worker default:"Surface audit pt2":hermes-swarm-loop \
  --worker default:"Deep audit pt1":hermes-swarm-loop \
  --verifier default \
  --synthesizer default \
  "Audit project at /path/to/project — N=33"

# 4. Dispatch workers (gateway runs them automatically)
hermes kanban dispatch

# 5. Check status
hermes kanban list
hermes kanban tail  # Live stream task events

# 6. After workers complete, verifier runs, then synthesizer
# 7. Check synthesized report
hermes kanban show <synthesizer_task_id>
```

---

## Prerequisites

- Hermes Agent v0.15+ installed and authenticated
- Model configured (DeepSeek V4 Flash / Claude / GPT / Gemini)
- Gateway running: `hermes gateway start`
- Kanban board initialized (happens automatically on first `hermes kanban` command)
- Sufficient API budget for N parallel agents

---

## Swarm API (The Core Mechanism)

All agent spawning uses the native **Hermes Kanban Swarm v1** API:

```
hermes kanban swarm \
  --worker PROFILE:TITLE[:SKILL,SKILL] \    # Repeatable for N workers
  --verifier PROFILE \                       # Verifies all outputs pass gate
  --synthesizer PROFILE \                    # Combines verified outputs
  [--tenant TENANT] \
  "Swarm goal description"
```

The swarm creates a DAG:
```
Root → Workers (parallel, N) → Verifier (gate) → Synthesizer → Done
```

**Why kanban swarm instead of delegate_task:**
- `hermes kanban swarm` spawns **true parallel processes** — each worker is an independent Hermes process
- Workers run in **isolated workspaces** with their own filesystem
- The **verifier** acts as a quality gate — workers don't advance until verified
- The **synthesizer** combines outputs into a single deliverable
- **No concurrency limit** — kanban dispatch spawns as many as the system can handle
- Each worker can load **skills** (via `:SKILL,SKILL` suffix)

---

## The Rules

### Rule 1: Three-Point Development Loop

Every iteration: AUDIT → IMPROVE → REVIEW. Never skip a point. Between each point there is an **aggregation step** — findings from parallel workers are deduplicated and merged before advancing.

**AUDIT (N agents via `hermes kanban swarm --worker ...`):**

N=33 recommended for first cycle. Distribution:
- 11 workers: Surface audit — syntax, types, structure, TODOs, dead code, imports, lint
- 11 workers: Deep audit — logic, state management, data flow, error handling, edge cases
- 11 workers: Exhaustive audit — all files, all paths, documentation gaps, API contracts

Command:
```bash
hermes kanban swarm \
  --worker default:"Surface audit 1/11":hermes-swarm-loop \
  --worker default:"Surface audit 2/11":hermes-swarm-loop \
  ... (11 surface workers) \
  --worker default:"Deep audit 1/11":hermes-swarm-loop \
  ... (11 deep workers) \
  --worker default:"Exhaustive audit 1/11":hermes-swarm-loop \
  ... (11 exhaustive workers) \
  --verifier default \
  --synthesizer default \
  "AUDIT phase — project at /path — 33 agents"
```

**Aggregation GATE:** After all AUDIT workers complete and verifier passes, the synthesizer produces a deduplicated `AUDIT_REPORT.md`. If conflicting findings exist, they are flagged for human resolution.

**IMPROVE (N agents via swarm):**
- Workers apply fixes from the deduplicated audit report
- Each fix is git-committed in its worker workspace
- Verifier checks: did the fix actually solve the issue without breaking anything?
- Synthesizer: merges all fixes into the main branch

**REVIEW (N agents via swarm):**
- Workers run automated checks (typecheck, lint, test, build)
- Workers perform manual logic review (read through each change)
- Verifier GATE: all checks must pass. Failure → findings sent back to IMPROVE.
- Synthesizer: produces `REVIEW_REPORT.md` — pass/fail per finding with evidence

### Rule 2: Three-Point Hunting Loop

Runs AFTER Loop 1 completes. No overlap between L1, L2, L3 levels.

**BUG HUNT (N agents per depth):**
- **L1: Syntax & surface** — null pointer dereferences, type mismatches, off-by-one errors
- **L2: Deep runtime** — race conditions, memory leaks, state corruption, deadlocks
- **L3: Heisenbugs & cascades** — concurrency anomalies, protocol violations, edge case cascades

**ARCHITECTURE HUNT (N agents per depth):**
- **L1: Structure** — file organization, naming, directory layout
- **L2: Coupling** — SOLID violations, dependency injection, module boundaries
- **L3: Scale** — scalability bottlenecks, CAP violations, distributed systems issues

**SECURITY HUNT (N agents per depth):**
- **L1: Surface** — hardcoded secrets, missing auth, exposed endpoints
- **L2: OWASP** — XSS, CSRF, SQL injection, path traversal, IDOR, SSRF
- **L3: Advanced** — cryptography flaws, side channels, supply chain risks

**GATE:** After each depth level, the verifier checks if findings are real (not false positives). Synthesizer produces `HUNT_REPORT.md`.

### Rule 3: Three-Point Simplicity & Consolidation Loop

Runs AFTER Loop 2 completes.

**Point 1: Dead Code Audit + Consolidation (NOT destruction)**
1. Find dead code, redundant functions, duplicates
2. **Reposition** — move to better location
3. **Consolidate** — merge duplicates into shared utilities
4. **Refactor** — slight architectural repositioning, no rewrites
5. Document why consolidated code exists

**Point 2: Operational Occam's Razor**
1. Testing bottlenecks — slow/flaky tests
2. CI/CD inefficiencies
3. Build/deploy slowdowns
4. Tooling overhead

**Point 3: PRD Alignment Audit (bridge back to Loop 1)**

This is ALIGNMENT, not a fourth loop:

1. Recall the original PRD — revisit vision doc, requirements, goals
2. **Compare HAP** (Has Actually Produced — current codebase) vs PRD vision
3. Account for Loop 1 & 2 changes — how dev/hunting changed the plan
4. **Identify PRD gaps** — what doesn't align? Missing features? Wrong direction?
5. **Triage gaps** — distinguish intentional descopes from genuine gaps
6. **Feed genuine gaps into Loop 1** as new AUDIT findings
7. **Repeat** — go back to Loop 1 with aligned findings

**GATE:** Verifier checks that PRD gaps are real (not hallucinations). Synthesizer produces aligned AUDIT seeds for next Loop 1.

### Rule 4: Cross-Model Review

**Core principle: "A loop can DRIVE, it cannot ACQUIT"**

The executor checks **execution completeness**. The reviewer (different model family) checks **quality and correctness**.

- Executor: DeepSeek (fast execution)
- Reviewer: Different model family (Claude, GPT, Gemini — whichever is available)
- Review at: end of each loop type, AND at self-reflection jury (every 3 cycles)

**When cross-model is unavailable:**
- Self-review with adversarial prompt: "pretend you are a hostile reviewer"

### Rule 5: Hive Swarm via Kanban

All parallel agent spawning uses `hermes kanban swarm`:

**Swarm distribution by scale:**

| Scale | Workers/Point | Command | Verifier | Synthesizer |
|-------|-------------|---------|----------|-------------|
| Small | 33 | 11 per sub × 3 subs | `default` | `default` |
| Medium | 100 | ~33 per sub | `default` | `default` |
| Large | 400 | ~133 per sub | `default` | `default` |
| Maximum | 999 | ~333 per sub | `default` | `default` |

**Each phase is a separate swarm invocation:**

```bash
# Phase 1: AUDIT (33 workers)
hermes kanban swarm --worker ...×33 --verifier default --synthesizer default "AUDIT"

# Phase 2: IMPROVE (33 workers)
hermes kanban swarm --worker ...×33 --verifier default --synthesizer default "IMPROVE"

# Phase 3: REVIEW (33 workers)
hermes kanban swarm --worker ...×33 --verifier default --synthesizer default "REVIEW"
```

**Note:** The 999-agent ceiling is a project goal, not a current implementation limit. Start at 33 and scale up as the Hermes Kanban infrastructure matures. Current practical limit is ~33 concurrent workers.

### Rule 6: Self-Reflection Jury

After every 3 full cycles, run self-reflection on 5 dimensions:

1. **Code Quality** — readability, maintainability, test coverage, duplication (0-1)
2. **Architecture** — design quality, scalability, SOLID, modularity (0-1)
3. **Security** — vulnerability surface, threat model coverage (0-1)
4. **Completeness** — full PRD coverage, all features done (0-1)
5. **Novelty** — innovative approach vs rehashing (0-1)

**Scoring:**
| Range | Verdict | Action |
|-------|---------|--------|
| All ≥ 0.85, flaws < 5, improving ≥ 3 cycles | MASTERPIECE | SHIP + GITHUB |
| Any ≥ 0.7, any < 0.85 | FLAWED — needs work | LOOP AGAIN on weakest dimension |
| Any < 0.7 | FLAWED — critical deficiency | LOOP AGAIN with new strategy |
| ≥ 3 cycles with < 5% improvement each | CAN'T IMPROVE | STOP + plateau analysis |

The jury uses cross-model review: executor scores, reviewer independently scores, then resolves.

### Rule 7: YOLO Mode

When active:
- `hermes kanban dispatch` spawns all workers immediately
- No confirmation dialogs
- Maximum velocity
- Workers auto-approve write_file, git push, deployments

Activation: Set `YOLO=true` in environment or pass in task description.

### Rule 8: Error Recovery

Escalation chain for failures:

1. **Worker crash/timeout** (hermes kanban list shows crashed/timed out):
   - Gateway auto-reclaims and retries (up to `--max-retries 2`)
   - If 3× retry fails: worker is blocked, flagged for human review

2. **Verifier rejection** — findings don't pass quality gate:
   - New swarm spawned with findings as input
   - Rejected workers' outputs are preserved for debugging

3. **Circuit breaker** — 3+ consecutive cycles with zero improvement:
   - Skip to self-reflection immediately
   - If CAN'T IMPROVE → STOP with plateau report
   - If FLAWED → switch strategy: try cross-model review first

4. **State corruption** — kanban SQLite DB is ACID-compliant. All task state is durable.

### Rule 9: Eat Your Own Dogfood

Run the framework on itself:

```bash
hermes kanban boards create swarm-dogfood
hermes kanban boards switch swarm-dogfood

# AUDIT phase — 33 workers
hermes kanban swarm \
  --worker default:"Surface SKILL.md":hermes-swarm-loop \
  --worker default:"Surface README.md":hermes-swarm-loop \
  ... (33 total) \
  --verifier default \
  --synthesizer default \
  "Audit Hermes Swarm Loop framework v4.0.0"

# IMPROVE phase
hermes kanban dispatch
# Wait for completion, then apply fixes

# REVIEW phase
hermes kanban swarm --worker ... --verifier default --synthesizer default "Review fixes"

# HUNTING phase
hermes kanban swarm --worker ... --verifier default --synthesizer default "Hunt framework bugs"

# SIMPLICITY phase
hermes kanban swarm --worker ... --verifier default --synthesizer default "Consolidate framework"

# Self-reflection
hermes kanban swarm --worker ... --verifier default --synthesizer default "Self-reflect v4.0.0"

# Push to GitHub
git add -A && git commit -m "feat: v4.0.0" && git push
```

---

## Comparison: vs Original Ralph

| Feature | Ralph (snarktank) | Hermes Swarm Loop |
|---------|-------------------|-------------------|
| Agent spawning | Sequential subprocess | `hermes kanban swarm` — true parallel |
| Workspaces | Single directory | Isolated per worker |
| Gate mechanism | `promise>COMPLETE` | Verifier + Synthesizer DAG |
| Concurrency | 1 agent | 33→999 workers per phase |
| Scalability | Manual retry | Gateway auto-dispatch |
| Cross-model review | None | Executor ≠ Reviewer jury |
| Error recovery | Crash = restart | Retry, circuit-breaker, block |
| Self-reflection | Pass/fail | 5-dimension scoring |
| Simplicity audit | None | Dead code + Occam + PRD align |

---

## Known Limitations (v4.0.0)

- **Max concurrent workers:** Limited by `kanban.dispatch_interval_seconds` (default 60s) and system resources. Practical max ~33 concurrent on a single VPS. The 999-worker ceiling is aspirational for multi-node deployments.
- **Kanban board required:** Each project needs its own board. Switch via `hermes kanban boards switch`.
- **Gateway must run:** `hermes gateway start` — without it, tasks queue but never execute.
- **Task artifacts:** `scratch` workspaces are ephemeral. For persistent reports, write to the project directory.
- **Cross-model review:** Currently requires manual model switching. Future: profile-level model config per worker.
