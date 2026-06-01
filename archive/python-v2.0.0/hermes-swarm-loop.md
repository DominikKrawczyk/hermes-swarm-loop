---
name: hermes-swarm-loop
description: "3x3 Ralph Loop for Hermes + DeepSeek. 2 loop types: AUDIT→IMPROVE→REVIEW (dev) + BUGS→ARCHITECTURE→SECURITY (hunt). 3x sub-iterations each. 400-agent swarm. Self-reflection gates masterpiece. YOLO mode. Build anything."
version: 1.0.0
author: Edward Puszczyk
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ralph-loop, swarm, multi-agent, deepseek, iteration, hunting, self-reflection]
    related_skills: [claude-code, codex, opencode]
---

# Hermes Swarm Loop — Get Shit Done

The 3×3 Ralph Loop for Hermes + DeepSeek. Two interleaved loop types, each with 3 points × 3 sub-iterations × N parallel agents. Self-reflection determines masterpiece vs more iterations. 400-agent hive swarm. YOLO mode. Build blockchain, infrastructure, anything.

## Core Architecture — The 2 Types of 3-Loops

```
┌─────────────────────────────────────────────────────────┐
│              HERMES SWARM LOOP                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  LOOP TYPE 1 — DEVELOPMENT                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  AUDIT   │→ │ IMPROVE  │→ │  REVIEW  │→ LOOP AGAIN │
│  │  ×3 sub  │  │  ×3 sub  │  │  ×3 sub  │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│         ↓              ↓              ↓                │
│  ┌──────────────────────────────────────┐              │
│  │  LOOP TYPE 2 — HUNTING (parallel)    │              │
│  │  ┌──────┐  ┌──────────┐  ┌────────┐ │              │
│  │  │ BUGS │  │ARCHITECT │  │SECURITY│ │              │
│  │  │×3glb │  │  ×3glb   │  │ ×3glb  │ │              │
│  │  └──────┘  └──────────┘  └────────┘ │              │
│  └──────────────────────────────────────┘              │
│                         ↓                              │
│  ┌──────────────────────────────────────┐              │
│  │  SELF-REFLECTION                     │              │
│  │  → MASTERPIECE? → SHIP + PUSH GITHUB │              │
│  │  → FLAWED?      → LOOP AGAIN (N+1)  │              │
│  │  → CAN'T IMPROVE? → STOP, REPORT     │              │
│  └──────────────────────────────────────┘              │
│                                                         │
│  400 AGENT HIVE SWARM (parallel × agent type)          │
│  YOLO MODE (auto-approve all)                          │
└─────────────────────────────────────────────────────────┘
```

## The Rules

### Rule 1: Three-Point Development Loop

Every iteration follows AUDIT → IMPROVE → REVIEW. Each point spawns 3 sub-iterations (×3 multiplier). Never skip a point.

**AUDIT (×3 sub):**
1. Read all code, understand architecture
2. Find what's implemented, what's missing, what's broken
3. Generate actionable findings with exact file:line references
4. Sub-iteration 1: Surface-level audit (syntax, types, structure)
5. Sub-iteration 2: Deep audit (logic, state, data flow)
6. Sub-iteration 3: Exhaustive audit (edge cases, error paths, all files)

**IMPROVE (×3 sub):**
1. Fix everything AUDIT found, prioritized by severity
2. Implement missing features from the goal
3. Refactor and optimize
4. Sub-iteration 1: Critical fixes (security, crashes, data loss)
5. Sub-iteration 2: Feature implementation
6. Sub-iteration 3: Polish, performance, docs

**REVIEW (×3 sub):**
1. Verify all changes are correct
2. Check nothing is broken
3. Validate against the goal/requirements
4. Sub-iteration 1: Automated checks (lint, test, typecheck)
5. Sub-iteration 2: Logic review
6. Sub-iteration 3: Final quality gate

### Rule 2: Three-Point Hunting Loop (Runs in Parallel)

Simultaneously with the development loop, run 3 hunt types. Each has 3 depth levels.

**BUG HUNT (×3 depths):**
1. Level 1: Syntax errors, null pointers, type mismatches
2. Level 2: Race conditions, memory leaks, state corruption
3. Level 3: Heisenbugs, concurrency deadlocks, protocol violations

**ARCHITECTURE HUNT (×3 depths):**
1. Level 1: File organization, naming, patterns
2. Level 2: Coupling, cohesion, SOLID, design patterns
3. Level 3: Scalability, distributed systems, CAP violations

**SECURITY HUNT (×3 depths):**
1. Level 1: Hardcoded secrets, basic injection, missing auth
2. Level 2: CSRF, XSS, SQL injection, path traversal, IDOR
3. Level 3: Cryptography flaws, side channels, supply chain

### Rule 3: Hive Swarm

Spawn N agents in parallel for each sub-iteration. N scales with project complexity. Default: 400 agents per full cycle. Distribution:

| Phase | Agents | Purpose |
|-------|--------|---------|
| AUDIT | 60 | 3 subs × 20 agents each |
| IMPROVE | 120 | 3 subs × 40 agents each |
| REVIEW | 60 | 3 subs × 20 agents each |
| BUG HUNT | 60 | 3 depths × 20 agents |
| ARCH HUNT | 50 | 3 depths × ~17 agents |
| SECURITY HUNT | 50 | 3 depths × ~17 agents |
| **Total** | **400** | |

### Rule 4: Self-Reflection

After each 3-point cycle (both loops), reflect on 5 dimensions:

1. **Code Quality**: Readability, maintainability, test coverage
2. **Architecture**: Design quality, trade-offs, scalability
3. **Security**: Vulnerability surface, threat model
4. **Completeness**: Does it actually solve the problem?
5. **Novelty**: Is it innovative or rehashing?

**Decision Matrix:**
- All 5 ≥ 0.85 + flaws < 5 + trend improving → **MASTERPIECE** → ship + push
- Any < 0.7 or flaws > 10 → **LOOP AGAIN** with focus on weakest dimension
- Stable with no improvement for 3 cycles → **CAN'T IMPROVE** → stop, report

### Rule 5: YOLO Mode (Auto-Approve)

When `--yolo` is active:
- No permission prompts
- No confirmation dialogs
- Auto-approve all file writes
- Auto-approve all tool calls
- Maximum velocity, zero brakes

### Rule 6: Context Accumulation

Findings, changes, and learnings accumulate across iterations. The working context includes:
- `swarm_state.json` — full iteration history
- `progress.md` — append-only learnings
- `findings/` — per-hunt findings by cycle
- Git history — all code changes

### Rule 7: Exit Conditions

An iteration cycle completes when:
1. All 3 points of Loop 1 complete (with 3 sub-iterations each)
2. All 3 points of Loop 2 complete (with 3 depths each)
3. Self-reflection evaluates the combined result

The full loop exits when:
- MASTERPIECE detected → push to GitHub, report
- MAX_CYCLES reached → report, save state
- User interrupts → save state for resume

## How to Use

### As a Skill (loaded in Hermes):
```
Load the hermes-swarm-loop skill and run a 3x3 Ralph Loop on /path/to/project
```

### As a CLI:
```bash
python launch.py --name "MyBlockchain" --desc "PoS blockchain" --model deepseek-v4-flash
```

### As a System Prompt:
Copy the Rules section above into your agent's system prompt.

## vs Original Ralph

| Feature | Original Ralph | Hermes Swarm Loop |
|---------|---------------|-------------------|
| Loop type | Linear (1 task → check → repeat) | 3-point (AUDIT→IMPROVE→REVIEW) |
| Multiplier | 1× | 3×3×N (3 points × 3 subs × agents) |
| Hunt types | None | Bugs, Architecture, Security |
| Agents per cycle | 1 | 400 |
| Self-reflection | Pass/fail only | 5-dimension masterpiece detection |
| YOLO mode | No | Yes |
| Model support | Claude only | Hermes + DeepSeek + any |
| Eat own dogfood | No | Yes (runs on itself) |
