# Hermes Swarm Loop

**3 × 3 × 11** — Phase 0 + Phase 1-3 + Simplicity. Cycle 1: BUILD, 2+: iterate.

```
Phase 0: PRD BUILD — 66 agents (research + questions + 33+33) — one-time, until full PRD done
Phase 1: ARCHITECTURE 11 + SETUP 11 + CODE GENERATION 11
Phase 2: AUDIT 11 + IMPROVE 11 + REVIEW 11
Phase 3: BUGS 11 + ARCH 11 + SECURITY 11
Simplicity: Dead Code 11 + Occam 11 + PRD Alignment 11

Cycle 1: BUILD | Cycle 2+: iterate
PRD Align → feeds back to BUILD (similar to IMPROVE)
Gate: 11 per point | Forced points | Auto-detect | YOLO default ON | Scale 11→999
```

## How It Works

1. **Phase 0** — PRD BUILD (66 agents, one-time). Defines the project.
2. **Phase 1-3** — 3 points each × 11 agents = 33 agents per phase.
3. **Simplicity** — Dead Code + Occam + PRD Align → back to Phase 0.
4. **Cycle 1** = BUILD from scratch. **Cycle 2+** = iterate with self-reflection.
5. **Gate 11** — verifier passes before next point.
6. **YOLO default ON** — auto-approve all. Scale 11→999.

## Installation

```bash
hermes skill install hermes-swarm-loop
```

Or clone the repo:

```bash
git clone https://github.com/DominikKrawczyk/hermes-swarm-loop.git
```

## Usage

Load the skill and run:

```
Phase 0: PRD BUILD on this project
→ 66 agents define scope, requirements, architecture
→ Output: full PRD document

Phase 1-3: iterate on code
→ 33 agents per phase, 11 per point
→ Gate checks between each point
→ Simplicity trim at end of cycle
```

## Dogfood

This framework runs **on itself**. After Phase 0 PRD is done, Phase 1-3 improve the framework SKILL.md and supporting scripts.
