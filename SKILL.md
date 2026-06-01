---
name: hermes-swarm-loop
description: "3 loops × 3 points × 11 agents. Loop 1: Development (AUDIT→IMPROVE→REVIEW). Loop 2: Hunting (BUGS→ARCH→SECURITY). Loop 3: Simplicity (Dead Code Consol→Occam→PRD Align→back to Loop 1). First cycle: Phase 0 Foundation build (PRD 66 agents + Arch 11 + Setup 11). Then 3 loops iterate. Self-reflection: masterpiece/flawed/cannot-improve. YOLO."
version: 5.0.0
author: Edward Puszczyk
github: DominikKrawczyk
license: MIT
---

# Hermes Swarm Loop — 3 Loops × 3 Points × 11 Agents

## Structure

```
CYCLE 1 (BUILD):
  Phase 0: Foundation (PRD Build + Architecture + Setup)
    → Point 1: PRD BUILD — 66 agents (33 research + 33 build)
    → Point 2: ARCHITECTURE — 11 agents
    → Point 3: SETUP — 11 agents
  → Loop 1: DEVELOPMENT (AUDIT → IMPROVE → REVIEW) — 33 agents
  → Loop 2: HUNTING (BUGS → ARCH → SECURITY) — 33 agents
  → Loop 3: SIMPLICITY (Dead Code → Occam → PRD Align → back to Loop 1)

CYCLE 2+ (ITERATE):
  → Loop 1: DEVELOPMENT (with PRD-aligned findings from Loop 3)
  → Loop 2: HUNTING
  → Loop 3: SIMPLICITY + PRD ALIGNMENT → back to Loop 1
  → After cycle 3: Self-reflection jury
```

## Phase 0: Foundation (Cycle 1 Only)

### Point 1: PRD BUILD (66 agents)
FIRST action. Ask user for PRD via clarify tool (10+ questions). Save ALL user input as 1:1 quotations without loss. Spawn 33 research agents. After research: spawn 33 build agents. Format full professional PRD document.

### Point 2: ARCHITECTURE (11 agents)
### Point 3: SETUP (11 agents)

## Loop 1: Development (AUDIT → IMPROVE → REVIEW)
3 points × 11 agents each. Every iteration follows AUDIT → IMPROVE → REVIEW. Never skip a point.

### Point 1: AUDIT (11 agents)
Audit what's implemented. 11 agents examine codebase for: surface issues, deep logic errors, exhaustive edge cases.

### Point 2: IMPROVE (11 agents)
11 agents fix all findings from AUDIT. Critical fixes first, then features, then polish.

### Point 3: REVIEW (11 agents)
11 agents verify: automated checks, manual logic review, final quality gate.

## Loop 2: Hunting (BUGS → ARCH → SECURITY)
Runs AFTER Loop 1. 3 points × 11 agents each.

### Point 1: BUGS (11 agents) — hunt hidden errors
### Point 2: ARCHITECTURE (11 agents) — hunt architectural flaws
### Point 3: SECURITY (11 agents) — hunt security vulnerabilities

## Loop 3: Simplicity & Consolidation
Runs AFTER Loop 2. 3 points × 11 agents each. Feeds back into Loop 1.

### Point 1: Dead Code Audit + Consolidation (11 agents)
NOT destruction. Consolidate and leverage scale. NOT simplification but refactor audit + repositioning slight architectural flaws. Find dead code, redundant functions, duplicates. Move to archive, merge into shared utilities, document.

### Point 2: Operational Occam's Razor (11 agents)
Reduce testing/simulation bottlenecks. Find and eliminate operational complexity.

### Point 3: PRD Alignment (11 agents) → back to Loop 1
"Get To A visionary PRD reminiscence." Audit HAP (Has Actually Produced — current codebase) vs PRD vision. Account for all changes from Loop 1 and Loop 2. This is ALIGNMENT, not further loops. PRD gap errors → feed into Loop 1 Point 1 as new AUDIT findings.

## First Cycle: BUILD ONLY
Phase 0 Foundation + 3 loops run once with no iteration logic. Just build.

## Iteration Logic (Cycle 2+)
- After each full cycle (Loops 1→2→3): self-reflection on 6 dimensions
- Gate mastery: minimum 3 full 3×3 cycles, findings diversified across PRD areas
- MASTERPIECE (all 6 ≥ 0.85, flaws < 5, improving ≥ 3 cycles, diversified) → SHIP + GITHUB
- FLAWED (any < 0.7 or flaws > 10 or not diversified) → LOOP AGAIN
- CAN'T IMPROVE (3 cycles flat, no improvement) → STOP

## Forced Points
Each loop forces every point exactly. No skipping. No shortcuts. Gate at 11 agents per point — verifier must pass before next point starts.

## Scale
Start at 11 agents per point. Scale up to max 999. No hard cap at 400 — 11/33 better approach, iterate up.
