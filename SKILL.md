---
name: hermes-swarm-loop
description: "Phase 0: PRD BUILD 66 — Phase 1-3: 3 points × 11 agents each — Simplicity → Phase 0 — Cycle 1 BUILD, 2+ iterate"
version: 6.0.0
author: Edward Puszczyk
github: DominikKrawczyk
license: MIT
---

# Hermes Swarm Loop — 3 × 3 × 11

```
Phase 0: PRD BUILD — 66 agents (research + questions + 33+33) — one-time, until full PRD done
Phase 1: ARCHITECTURE 11 + SETUP 11 + CODE GENERATION 11
Phase 2: AUDIT 11 + IMPROVE 11 + REVIEW 11
Phase 3: BUGS 11 + ARCH 11 + SECURITY 11
Simplicity: Dead Code 11 + Occam 11 + PRD Alignment 11

Cycle 1: BUILD | Cycle 2+: iterate
Mastery Gate: diversified non-local per PRD area — check across all areas, not just one
Auto Skill Update: after each phase, skill learns & evolves
Gate: 11 per point | Forced points | Auto-detect | YOLO default ON | Scale 11→999
```

## Phase 0 — PRD BUILD (66 agents, one-time)
66 agents: 33 research + 33 build. Runs until full PRD is complete.

→ Auto Skill Update: skill saves PRD structure and findings
→ **Mastery Gate**: diversified non-local check across all PRD areas

## Phase 1 — Development (3 points × 11 agents)
- ARCHITECTURE: architecture design
- SETUP: project setup
- CODE GENERATION: implementation start

→ Auto Skill Update: skill saves architecture decisions, setup patterns
→ **Mastery Gate**: cross-check arch decisions against PRD areas

## Phase 2 — Quality (3 points × 11 agents)
- AUDIT: code audit
- IMPROVE: improvements
- REVIEW: quality gate

→ Auto Skill Update: skill saves audit findings, improvement patterns
→ **Mastery Gate**: verify improvements don't break other PRD areas

## Phase 3 — Hunting (3 points × 11 agents)
- BUGS: bug hunting
- ARCH: architecture review
- SECURITY: security audit

→ Auto Skill Update: skill saves bug patterns, security rules
→ **Mastery Gate**: cross-check security/arch findings across domains

## Simplicity (3 points × 11 agents)
- Dead Code: consolidate, not destroy
- Occam: bottlenecks reduction
- PRD Alignment: gaps drive rebuild → Phase 0

→ Auto Skill Update: skill saves simplification rules
→ **Mastery Gate**: verify simplicity doesn't sacrifice PRD coverage

## Mastery Gate Logic
Not a simple pass/fail. For each PRD area, the gate spawns diversified checks across OTHER areas (non-local). E.g. when Phase 1 ARCH finishes, the gate tests architecture against security, scaling, UX — not just architecture itself.

## Auto Skill Update
After each phase completes, skill_manage('patch') is called to update SKILL.md with:
- Key findings from the phase
- New rules/patterns discovered
- Updated pitfalls
- Phase completion status

## Rules
- **Cycle 1: BUILD** — no iteration, just build from scratch
- **Cycle 2+: iterate** — self-reflection after each cycle
- **Forced points** — every point runs, no skipping
- **Gate 11** — verifier must pass before next point (under Mastery Gate)
- **Auto-detect** — project size auto-determines agent count
- **YOLO default ON** — auto-approve all, no manual confirmation
- **Scale: 11→999** — no hard cap on agent count
