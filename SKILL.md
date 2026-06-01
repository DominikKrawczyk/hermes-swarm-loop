---
name: hermes-swarm-loop
description: "3×3×3×N Hermes Swarm Loop — Development (AUDIT→IMPROVE→REVIEW) × Hunting (BUGS→ARCH→SECURITY) × Simplicity/Consolidation (REFACTOR→OCCAM→PRD-ALIGN) × N agents (33→999). Cross-model review. Self-reflection: masterpiece/flawed/cannot-improve. YOLO mode. Build blockchain, infra, apps."
version: 3.0.0
author: Edward Puszczyk
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [ralph-loop, swarm, multi-agent, deepseek, iteration, hunting, self-reflection, yolo, cross-model-review]
    related_skills: [claude-code, codex, hermes-agent, subagent-driven-development]
---

# Hermes Swarm Loop — 3×3×3×N

## When to Use

This skill defines the **3-Loop Hermes Ralph** — a prompt-based methodology for building anything with autonomous agent iteration. Use when:

- Building **blockchain, huge infrastructure, complex applications** from scratch
- You want the agent to iterate in **3-point cycles × 3 loop types × 3 sub-iterations × N agents** until truly done
- You need **33→999 agents** working in parallel (hive swarm)
- You want automatic **bug hunting, architecture review, security scanning, AND simplicity/consolidation audit** built into the iteration cycle
- You need **cross-model review** — executor (DeepSeek) + reviewer (different model family) — to break self-play blind spots
- You need **self-reflection** to determine if something is a masterpiece, still flawed, or cannot be further improved
- **YOLO mode**: zero brakes, auto-approve everything, maximum velocity

This is a **prompt methodology** — rules the agent follows, not a Python program. The agent executes the rules using its own tools (`delegate_task`, `terminal`, `read_file`, `write_file`, etc.).

**Inspiration:** Ralph Loop (snarktank/ralph 19.8k⭐) × Ralphy (michaelshimeles/ralphy 2.9k⭐) × ARIS (wanshuiyin/ARIS 11.2k⭐) × Hive (aden-hive/hive 10.5k⭐) — combining the best of all.

---

## Core Architecture — The 3 Loop Types

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                         HERMES SWARM LOOP — 3×3×3×N                                │
│                                                                                    │
│  ┌──────────────────────────────────────────────────────────────────────────┐      │
│  │  LOOP 1 — DEVELOPMENT          LOOP 2 — HUNTING        LOOP 3 —          │      │
│  │  (AUDIT→IMPROVE→REVIEW)        (BUGS→ARCH→SECURITY)    SIMPLICITY         │      │
│  │  × 3 sub-iterations each       × 3 depths each         & CONSOLIDATION    │      │
│  │                                                                           │      │
│  │  AUDIT ─┬── Sub 1: Surface     BUGS ─┬── L1: Syntax   1. Dead Code        │      │
│  │         ├── Sub 2: Deep                ├── L2: Race       Audit +          │      │
│  │         └── Sub 3: Exhaustive          └── L3: Heisen    Consolidate       │      │
│  │                                         bugs                              │      │
│  │  IMPROVE ┬─ Sub 1: Critical                                                  │      │
│  │          ├─ Sub 2: Feature     ARCH ─┬── L1: Structure  2. Occam's Razor    │      │
│  │          └─ Sub 3: Polish            ├── L2: Coupling    Bottlenecks        │      │
│  │                                      └── L3: Scale                          │      │
│  │  REVIEW ─┬─ Sub 1: Auto-verify                                                │      │
│  │          ├─ Sub 2: Manual logic    SEC ─┬── L1: Secrets  3. PRD ALIGNMENT   │      │
│  │          └─ Sub 3: Quality gate         ├── L2: OWASP      ← BACK TO        │      │
│  │                                         └── L3: Crypto     LOOP 1           │      │
│  └──────────────────────────────────────────────────────────────────────────┘      │
│                                    │                                               │
│                                    ↓                                               │
│  ┌──────────────────────────────────────────────────────────────────────────┐      │
│  │  SELF-REFLECTION — 5 dimensions × cross-model review jury                 │      │
│  │                                                                           │      │
│  │  Dimensions: Code Quality, Architecture, Security, Completeness, Novelty  │      │
│  │  Jury: Executor (one model) + Reviewer (different model family)          │      │
│  │                                                                           │      │
│  │  → MASTERPIECE (≥0.85, flaws <5, improving ≥3 cycles) → SHIP + GITHUB     │      │
│  │  → FLAWED (any <0.7 or flaws >10) → LOOP AGAIN (weakest dimension focus)  │      │
│  │  → CAN'T IMPROVE (3 cycles stable, no gain) → STOP + REPORT               │      │
│  └──────────────────────────────────────────────────────────────────────────┘      │
│                                                                                    │
│  SWARM CAPACITY: 33→999 agents via delegate_task                                  │
│  YOLO MODE: auto-approve all tool calls                                            │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Cycle Order

Always run in this sequence:

```
LOOP 1 (Development) → LOOP 2 (Hunting) → LOOP 3 (Simplicity & Consolidation)
                                                                    ↓
                                                          (Point 3: PRD Alignment)
                                                                    ↓
                                                            BACK TO LOOP 1 (aligned)
                                                                    ↓
                                                         SELF-REFLECTION JURY
                                                                    ↓
                                                    masterpiece? → SHIP + GITHUB
                                                    flawed? → LOOP AGAIN
                                                    can't improve? → STOP
```

---

## The Rules (Follow These Exactly)

### Rule 1: Three-Point Development Loop (Type 1)

Every iteration follows AUDIT → IMPROVE → REVIEW. Never skip a point.

**AUDIT (×3 sub-iterations, N/3 agents each):**

- **Sub 1: Surface audit** — syntax, types, structure, TODOs, dead code, imports, lint
- **Sub 2: Deep audit** — logic errors, state management, data flow, error handling, edge cases
- **Sub 3: Exhaustive audit** — all files, all paths, documentation gaps, API contracts, testing gaps

Output: `AUDIT_REPORT.md` with exact file:line references, severity, and actionable findings.

**IMPROVE (×3 sub-iterations, N/3 agents each):**

- **Sub 1: Critical fixes** — security, crashes, data loss, blocking bugs, compile errors
- **Sub 2: Feature implementation** — missing functionality, incomplete features, PRD gaps
- **Sub 3: Polish** — performance optimization, documentation, code quality, test coverage

Output: All findings from AUDIT are fixed. Git commit per sub-iteration.

**REVIEW (×3 sub-iterations, N/3 agents each):**

- **Sub 1: Automated verification** — typecheck, lint, test, build. All must pass.
- **Sub 2: Manual logic review** — verify correctness, read through changes, check edge cases
- **Sub 3: Final quality gate** — is everything clean? Nothing broken? Any regressions?

Output: `REVIEW_REPORT.md` — pass/fail per finding with evidence.

### Rule 2: Three-Point Hunting Loop (Type 2)

Runs AFTER Loop 1 completes. Each hunt type has 3 depth levels:

**BUG HUNT (×3 depths, parallel):**

- **Level 1: Syntax & surface** — syntax errors, null/undefined pointers, type mismatches, off-by-one, race conditions in obvious places
- **Level 2: Deep runtime** — race conditions, memory leaks, state corruption, incorrect API usage, deadlocks
- **Level 3: Heisenbugs & cascades** — concurrency deadlocks, protocol violations, edge case cascades, heisenbugs

**ARCHITECTURE HUNT (×3 depths, parallel):**

- **Level 1: Structure & naming** — file organization, naming conventions, basic patterns, directory layout
- **Level 2: Coupling & cohesion** — SOLID violations, dependency injection, module boundaries, tech debt
- **Level 3: Scale & distributed** — scalability bottlenecks, distributed systems issues, CAP violations, data flow

**SECURITY HUNT (×3 depths, parallel):**

- **Level 1: Surface vulnerabilities** — hardcoded secrets, basic injection, missing auth, exposed endpoints
- **Level 2: OWASP top 10** — CSRF, XSS, SQL/NoSQL injection, path traversal, IDOR, SSRF
- **Level 3: Advanced** — cryptography flaws, side channels, supply chain risks, zero-day patterns

Output: `HUNT_REPORT.md` — all findings with severity, impact, and fix recommendation.

### Rule 3: Three-Point Simplicity & Consolidation Loop (Type 3)

Runs AFTER Loop 2 completes.

**Point 1: Dead Code Audit + Consolidation (NOT destruction)**

DO NOT simply delete code. The goal is to **consolidate and leverage scale**:

1. Find dead code, redundant functions, duplicate implementations
2. **Reposition** — move to where it belongs, reorganize for clarity
3. **Consolidate** — merge duplicate logic into shared utilities
4. **Refactor** — slight architectural repositioning, not rewrites
5. Document why consolidated code exists for future reference

**Point 2: Operational Occam's Razor**

Find and eliminate operational complexity:

1. **Testing bottlenecks** — slow tests, flaky tests, integration test dead zones
2. **Simulation bottlenecks** — CI/CD pipeline inefficiencies
3. **Build/Deploy bottlenecks** — slow builds, unnecessary steps
4. **Tooling overhead** — too many configs, unnecessary abstractions

Output: `SIMPLICITY_REPORT.md` — each bottleneck with before/after improvement estimate.

**Point 3: PRD Alignment Audit (← go back to Loop 1)**

This is the **bridge back to Loop 1**. Do NOT treat this as a fourth loop point — it is ALIGNMENT:

1. **"Get To A visionary PRD reminiscence"** — recall the original PRD (vision doc, requirements, goals)
2. **Audit HAP (current codebase/state) vs PRD** — what exists vs what was envisioned
3. **Account for Loop 1 & Loop 2 changes** — how development and hunting modified the original plan
4. **PRD gap errors** — what doesn't align with the PRD? Missing features? Wrong direction?
5. **Feed gaps into Loop 1** — create new AUDIT findings from PRD gaps
6. **REPEAT** — go back to Loop 1 with aligned findings

This is ALIGNMENT, not further looping. The PRD gap errors become the seeds for the next cycle.

---

### Rule 4: Cross-Model Review (from ARIS)

**Core principle: "A loop can DRIVE, it cannot ACQUIT"**

The executor (doing the AUDIT/IMPROVE/REVIEW work) checks **execution completeness**. 
A separate reviewer (different model family) checks **quality and correctness**.

This breaks self-play blind spots — the same model reviewing its own work misses patterns.

**Implementation:**
- Executor: DeepSeek (fast execution, fluid work)
- Reviewer: Different model family (Claude, GPT, Gemini — whichever is available)
- Review happens at: end of each loop type (after Loop 1, after Loop 2, after Loop 3)
- Cross-model jury at: self-reflection phase

**When cross-model is not available:**
- Self-review with explicit adversarial mode: "pretend you are a hostile reviewer and find problems"

---

### Rule 5: Hive Swarm (33→999 Agents)

Spawn agents in parallel for each sub-iteration using `delegate_task()`.

**Swarm distribution by scale:**

| Scale | Total Agents | Distribution |
|-------|-------------|--------------|
| Small | 33 | 11× per loop (3 loops × 11 agents per sub-phase) |
| Medium | 100 | ~33 per loop |
| Large | 400 | ~133 per loop |
| Maximum | 999 | ~333 per loop |

**Distribution per loop (medium scale):**

| Phase | Agents | Method |
|-------|--------|--------|
| AUDIT (3 subs) | 33 | 11 agents per sub via delegate_task |
| IMPROVE (3 subs) | 33 | 11 agents per sub |
| REVIEW (3 subs) | 33 | 11 agents per sub |
| BUG HUNT (3 depths) | 33 | 11 agents per depth |
| ARCH HUNT (3 depths) | 33 | 11 agents per depth |
| SECURITY HUNT (3 depths) | 33 | 11 agents per depth |
| SIMPLICITY (3 points) | 33 | 11 agents per point |
| PRD ALIGNMENT | 33 | 33 agents across all PRD items |
| **Total per cycle** | **~300** | Adjust for scale |

Each agent task: `delegate_task(goal="Audit file X for Y", context="...", toolsets=["terminal","file"])`

**Start small (33) and scale up to 999 on subsequent cycles based on findings volume.**

---

### Rule 6: Self-Reflection Jury

After all 3 loops complete in one cycle, run self-reflection on 5 dimensions:

1. **Code Quality** — readability, maintainability, test coverage, duplication, consistency
2. **Architecture** — design quality, trade-offs, scalability, SOLID, modularity, coupling
3. **Security** — vulnerability surface, threat model coverage, defense depth, attack vectors
4. **Completeness** — does it solve the original PRD completely? All features? All edge cases?
5. **Novelty** — innovative approach or just rehashing? Does it advance the state?

**Cross-model jury process:**
1. Executor summarizes all changes per dimension (score 0-1 + evidence)
2. Reviewer independently evaluates (score 0-1 + evidence)
3. Jury resolves discrepancies → final score per dimension
4. Overall assessment

**3 possible outcomes:**
- **MASTERPIECE** (all 5 ≥ 0.85, flaws < 5, improvement trend over ≥3 cycles)
  → Push to GitHub, generate FINAL_REPORT.md, DONE
- **FLAWED** (any dimension < 0.7 or flaws > 10 or degrading trend)
  → LOOP AGAIN, focus next cycle on the weakest dimension(s)
- **CAN'T IMPROVE** (≥3 cycles with <5% improvement per cycle)
  → STOP gracefully, write STOP_REASON.md with analysis of plateau

---

### Rule 7: YOLO Mode

When active:
- Auto-approve ALL tool calls (file writes, bash, git push, deployments)
- No permission prompts, no confirmation dialogs, no safety brakes
- Maximum velocity
- Used for: "Get shit done" mode when you trust the agent completely

To activate: set `YOLO=true` in project config or pass as argument.

---

### Rule 8: Context Accumulation & Memory

- Accumulate findings, changes, and learnings across iterations
- Git history preserves all code changes (commit per sub-iteration)
- Memory file: `.hermes-swarm-loop/memory.json` tracks:
  - Current cycle number
  - Current loop type and point
  - Findings from each phase
  - Agent distribution used
  - Self-reflection scores per cycle
- When the agent loads the skill, it scans the memory file to determine where to continue

---

### Rule 9: Eat Your Own Dogfood

The framework improves ITSELF through the same 3×3×3×N loop:

1. Run Loop 1 (Development) on the framework code in `/opt/hermes-swarm-loop/`
2. Run Loop 2 (Hunting) — hunt for bugs, architectural flaws, security issues in the framework itself
3. Run Loop 3 (Simplicity & Consolidation) — dead code audit, Occam's Razor, PRD alignment
4. Self-reflect: is the framework itself a masterpiece?
5. Push improved framework to GitHub
6. Repeat from Step 1 with accumulated improvements

---

## How to Use

**As a skill (loaded via Hermes):**
```
Load the hermes-swarm-loop skill and run a 3×3×3×N Swarm Loop on /path/to/project — N=100, yolo mode
```

**As a system prompt:**
Copy Rules 1-9 into your agent's system prompt. The agent will follow the 3-loop pattern automatically.

**As a GitHub repo:**
Clone `github.com/DominikKrawczyk/hermes-swarm-loop` — the skill file IS the framework.

---

## Comparison: vs Original Ralph

| Feature | Ralph (snarktank) | Hermes Swarm Loop |
|---------|-------------------|-------------------|
| Loop structure | 1 task → implement → check → repeat | 3 loops × 3 points × 3 sub × N |
| Points per iteration | 1 story | 9 (3 dev + 3 hunt + 3 simplicity) |
| Multiplier | 1× | 3×3×3×N |
| Parallel agents | 1 | Up to 999 |
| Hunting | None | Bugs + Architecture + Security (×3 depths each) |
| Simplicity audit | None | Dead code consolidation + Occam's Razor + PRD Alignment |
| Review model | Self-review | Cross-model review (executor ≠ reviewer) |
| Self-reflection | Pass/fail on story | 5-dimension masterpiece/flawed/cannot-improve |
| Exit condition | All PRD stories pass | Masterpiece detected OR can't improve |
| Implementation | Bash script + prompt | Pure prompt/skill methodology |
| YOLO | No | Yes |
| Model agnostic | Claude/Amp | DeepSeek, Claude, GPT, Gemini, any |

---

## Quick Start

```bash
# Get the framework
git clone https://github.com/DominikKrawczyk/hermes-swarm-loop.git
cd hermes-swarm-loop

# Load the skill in Hermes
hermes load-skill hermes-swarm-loop

# Run on any project
hermes chat -q "Load hermes-swarm-loop and run 3-loop cycle on /path/to/project — N=33, yolo"

# Run on itself (eat dogfood)
hermes chat -q "Load hermes-swarm-loop and run 3-loop cycle on /opt/hermes-swarm-loop/ — N=33, yolo, auto-github-push"
```
