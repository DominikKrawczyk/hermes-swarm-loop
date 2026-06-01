---
name: hermes-swarm-loop
description: "Phase 0: PRD BUILD 66 — Phase 1-3: 3 points × 11 agents each — Simplicity → Phase 0 — Cycle 1 BUILD, 2+ iterate"
version: 6.2.0
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

**Execution:** Spawn 1-3 cross-check agents via `delegate_task`. Each agent checks a different non-local area. Score 7 dimensions (0-1): Correctness, Safety, Test Coverage, Consistency, Diversity, Efficiency, Clarity. Weighted total = sum(dim × w) with weights: Correctness 0.25, Safety 0.20, Test Coverage 0.15, Consistency 0.15, Diversity 0.10, Efficiency 0.10, Clarity 0.05. Thresholds: PASS ≥0.70, CROSS-CHECK 0.50-0.69, REVIEW 0.30-0.49, BLOCK <0.30. Average all agent scores for final verdict. On PASS: proceed. On CROSS-CHECK: fix gaps flagged by all scoring agents, then re-run. On REVIEW/BLOCK: abort cycle.

## Auto Skill Update
After each phase completes, `skill_manage('patch')` is called to update SKILL.md with:
- Key findings from the phase
- New rules/patterns discovered
- Updated pitfalls
- Phase completion status

**Execution:** Read the current SKILL.md, identify the section to update (e.g. "Rules" or add "Phase N Completion"), write the new insights as a patch. Bump the version number in frontmatter.

## Rules
- **Cycle 1: BUILD** — no iteration, just build from scratch
- **Cycle 2+: iterate** — self-reflection after each cycle
- **Forced points** — every point runs, no skipping
- **Gate 11** — verifier must pass before next point (under Mastery Gate)
- **Auto-detect** — project size auto-determines agent count (11/33/66/999)
- **YOLO default ON** — auto-approve cosmetic/reversible ops; always blocks destructive/security/cross-boundary
- **Scale: 11→999** — no hard cap on agent count

## Execution Guide

How to actually run each phase. Use the same pattern for all phases.

### Step 1: Research Agents
Identify 2-4 research angles for the current phase (e.g. arch, UX, security, scaling). Spawn via `delegate_task` batch mode (max 3 concurrent). Each agent reads the project files and outputs findings.

### Step 2: Build Agents
Based on research gaps, spawn 2-3 build agents. Each proposes concrete solutions. Use same `delegate_task` pattern.

### Step 3: Synthesize
Read all agent outputs, write the phase deliverable (PRD.md for Phase 0, design doc for Phase 1, etc.). Save to project directory.

### Step 4: Auto Skill Update
`skill_manage('patch')` the SKILL.md with: phase findings, new rules, updated pitfalls, version bump.

### Step 5: Mastery Gate
Spawn 1-3 cross-check agents via `delegate_task`. Each checks different non-local areas. Score 7 dimensions, average scores, compare to thresholds. Fix gaps on CROSS-CHECK, abort on BLOCK.

### Step 6: GitHub Push
Push updated files (SKILL.md, README.md, phase deliverable) via `gh api` blob→tree→commit→ref pipeline.

### Step 7: Next Phase
On Mastery Gate PASS, proceed to next phase. On CROSS-CHECK, fix and re-gate. On BLOCK, re-run the phase.

## Phase 0 Completion (v6.0.0)
Completed by 6 agents (3 research + 3 build) on the framework itself.
Key findings recorded in PRD.md:
- YOLO semantics: auto-approve zone list + always-block zone list + safety valve
- Mastery Gate: 7-dimension scoring, 4 thresholds, non-local cross-check algorithm
- Scaling: 3-tier hierarchy via delegate_task, adaptive micro-batching, content-addressable file safety
- Gate 11 ≠ Mastery Gate: Gate 11 is per-point verification; Mastery Gate is per-phase diversified cross-check

Mastery Gate result: **PASS** (0.7508 ≥ 0.70). 3 cross-check agents scored: 0.6475 (ARCH→SEC+SCALE), 0.7500 (SCALE→UX+ARCH), 0.8550 (GATES→ALL). Action items for Phase 1: security requirements, test strategy, CAS implementation, README YOLO consistency.

## Phase 1 Completion (v6.1.0)
Phase 1 completed via kanban swarm × 3 points × 11 agents = 33 workers + 3 verifiers + 3 synthesizers = 39 total tasks.
- ARCHITECTURE 11 ✅ — swarm topology, state machine, agent roles, gate engine, skill update protocol, workspace layout, kanban config, bootstrap plan, YOLO arch, PRD schema, diversity algo. All outputs in arch/
- SETUP 11 ✅ — workspace scripts, kanban automation, agent role scripts, templates, configs. Output in setup/, code/kanban_automation/, code/agent_roles/
- CODE GEN 11 ✅ — mastery_gate.py, phase_engine.py, queue_manager.py, skill_updater.py, synthesizer.py, yolo/ modules, src/hermes_swarm_loop/ package, bootstrap.py. All in code/, src/, setup/

Phase output: 9.4MB, 50+ Python files, full framework code generated.

## Phase 1 Pt3 Completion — Code Gen 11 (v6.2.0)

Completed by 1 agent (role index 8 — Kanban Automation) on task `t_413bcd5e`.
Key findings recorded in `code/kanban_automation/REGISTRY.md`:

### Architecture Decisions
- **ConfigRegistry** singleton holds BoardConfig + task templates, loaded from `board-config.yaml` and `task-templates.json` with missing-file fallback.
- **Deterministic Role Assignment**: `compute_role_index(task_index)` = `task_index % 11` (arch §8.1). All 4 phase maps (Phase 1/2/3/Simplicity) have exactly 11 roles per point.
- **Task Factory**: `create_point_tasks()` spawns 11 workers from templates, then creates Gate 11 verifier (depends on all workers), synthesizer (depends on verifier), and Mastery Gate (depends on all outputs). Auto-promotion handled natively by kanban parent/child links.
- **BoardManager**: Queries board via `kanban_show`, implements Gate 11 check with quorum rules (PASS ≥ all done, BLOCK < 80%).
- **Orchestrator**: Sequential point creation within a phase, each point depending on the previous point's verifier/synthesizer. Wait-for-completion with configurable timeout.
- **WorkspaceManager**: Supports scratch (temp, GC-able), dir (shared persistent), worktree (git worktree). Validation checks exist, writable, expected kind.
- **AutoPromoter**: Observability layer — `check_parents()` returns detailed status breakdown, `find_promotable()` batch-detects ready tasks.

### Created Artifacts
14 files, ~2,348 lines at `code/kanban_automation/`:
- 7 Python modules (config, task_factory, board_manager, orchestrator, workspace_manager, auto_promoter, init)
- 1 REGISTRY.md
- 6 test files (87 tests, 87 passing)

### Pitfalls Discovered
- **YAML loader must handle missing files gracefully**: `_load_yaml_simple` crashed on nonexistent paths. Fixed: check `os.path.isfile()` first.
- **Empty parent list is trivially "all done"**: A task with 0 parents is considered promoted. Correct behavior — wait_for_completion([]) returns True immediately.
- **kanban-based modules can only be tested in dry-run or unit-test mode**: The `kanban_create` and `kanban_show` tools only work inside a live running task. Test for PhaseResult shape and role assignment logic separately from board interaction.

### Key Rules Added
- Always use `dry_run=True` in tests that don't have a live kanban board.
- Config loaders must gracefully handle missing files (return defaults).
- Role definitions must have exactly 11 entries per point and no duplicates.

