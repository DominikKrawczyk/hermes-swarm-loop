---
name: hermes-swarm-loop
description: "Phase 0: PRD BUILD 66 — Phase 1-3: 3 points × 11 agents each — Simplicity → Phase 0 — Phase 2(HUNT)→Phase 3(FIX) swap loop, Phase 1 one-time"
version: 6.10.0
author: Edward Puszczyk
github: DominikKrawczyk
license: MIT
---

# Hermes Swarm Loop — 3 × 3 × 11

```\nPhase 0: PRD BUILD — 66 agents (research 22 + questions 22 + build 22) — one-time, until full PRD done\nPhase 1: ARCHITECTURE 11 + SETUP 11 + CODE GENERATION 11\nPhase 2: BUGS 11 + ARCH 11 + SECURITY 11 (HUNTING — find bugs FIRST)\nPhase 3: AUDIT 11 + IMPROVE 11 + REVIEW 11 (QUALITY — fix based on real bugs)\nSimplicity: Dead Code 11 + Occam 11 + PRD Alignment 11\n\nCycle 1: BUILD | Cycle 2+: HUNT→QUALITY swap loop\nMastery Gate: diversified non-local per PRD area — check across all areas, not just one\nAuto Skill Update: after each phase, skill learns & evolves\nGate: 11 per point | Forced points | Auto-detect | YOLO default ON | Scale 11→999\n```

## Phase 0 — PRD BUILD (66 agents, one-time)
66 agents: 22 research + 22 questions + 22 build. Runs until full PRD is complete.

→ Auto Skill Update: skill saves PRD structure and findings
→ **Mastery Gate**: diversified non-local check across all PRD areas

## Phase 1 — Development (3 points × 11 agents)
- ARCHITECTURE: architecture design
- SETUP: project setup
- CODE GENERATION: implementation start

→ Auto Skill Update: skill saves architecture decisions, setup patterns
→ **Mastery Gate**: cross-check arch decisions against PRD areas

## Phase 2 — Hunting (3 points × 11 agents) — NOW RUNS FIRST
- BUGS: bug hunting (find real bugs first)
- ARCH: architecture review
- SECURITY: security audit

→ Auto Skill Update: skill saves bug patterns, security rules
→ **Mastery Gate**: cross-check security/arch findings across domains

## Phase 3 — Quality (3 points × 11 agents) — NOW RUNS SECOND
- AUDIT: code audit (on ground truth after bug fixes)
- IMPROVE: improvements (fix based on real bugs found)
- REVIEW: quality gate

→ Auto Skill Update: skill saves audit findings, improvement patterns
→ **Mastery Gate**: verify improvements don't break other PRD areas

## Simplicity (3 points × 11 agents)
- Dead Code: consolidate, not destroy
- Occam: bottlenecks reduction
- PRD Alignment: gaps drive rebuild → Phase 0

→ Auto Skill Update: skill saves simplification rules
→ **Mastery Gate**: verify simplicity doesn't sacrifice PRD coverage

## Mastery Gate Logic
Not a simple pass/fail. For each PRD area, the gate spawns diversified checks across OTHER areas (non-local). E.g. when Phase 1 ARCH finishes, the gate tests architecture against security, scaling, UX — not just architecture itself.

**Execution:** Spawn 1-3 cross-check agents via `delegate_task`. Each agent checks a different non-local area. Score 7 dimensions (0-1): Correctness, Safety, Test Coverage, Consistency, Diversity, Efficiency, Clarity. Weighted total = sum(dim × w) with weights: Correctness 0.25, Safety 0.20, Test Coverage 0.15, Consistency 0.15, Diversity 0.10, Efficiency 0.10, Clarity 0.05. Thresholds: PASS ≥0.70, CROSS-CHECK 0.50-0.69, REVIEW 0.30-0.49, BLOCK <0.30. Average all agent scores for final verdict. On PASS: proceed. On CROSS-CHECK: fix gaps flagged by all scoring agents, then re-run. On REVIEW/BLOCK: abort cycle.

## Bootstrap Launcher (`bootstrap.py`)

Use `python3 bootstrap.py` as the entry point for any Hermes Swarm Loop run. It replaces the old `launch.sh` and handles all setup in a single deterministic pipeline before any `hermes kanban swarm` calls.

### 5-Stage Pipeline

| Stage | What It Does | CLI Flag Control |
|-------|-------------|------------------|
| **1 — Environment Check** | Verifies `hermes`, `python3`, `gh`, `git` on PATH; checks Python ≥ 3.10; checks `gh auth status` | Always runs |
| **2 — Database Init** | Creates/verifies `.swarm_state.db` with WAL mode; creates all 4 tables (`phase_state`, `point_state`, `yolo_state`, `event_log`); runs schema migrations | `--db-path` to override |
| **3 — Phase Setup** | Starts target phase as `running`; creates point records for all points in that phase | `--phase` (default: `development`) |
| **4 — YOLO Init** | Sets YOLO zone; caps `max_parallel` to zone limit; resets safety valve counters | `--yolo-zone` (default: `test`) |
| **5 — Launch** | Prints `hermes kanban swarm` commands for each point; saves config to DB + `.hermes_swarm_launch.json`; skippable with `--init-only` | `--init-only` to skip |

### Usage

```bash
# Standard launch (default: development phase, test zone, 33 agents)
python3 bootstrap.py --project-name "MyApp" --project-desc "Build X"

# PRD BUILD phase with staging YOLO
python3 bootstrap.py --project-name "MyApp" --project-desc "Build X" \
  --phase prd_build --yolo-zone staging --max-agents 66

# Setup only (no launch commands printed)
python3 bootstrap.py --project-name "MyApp" --project-desc "Build X" --init-only
```

### Behavior Details

- **Agent cap respect**: If `--max-agents` exceeds the current YOLO zone's max, it warns and caps automatically (e.g., staging max is 33, so `--max-agents 66` becomes 33).
- **Re-entrant**: Running bootstrap again on the same DB updates the phase state and regenerates points. Use `--init-only` for re-setup without launch output.
- **Config persistence**: Each launch saves to the `launch_config` table in `.swarm_state.db` and to `.hermes_swarm_launch.json` for tooling to consume.

### Integration with Kanban Swarm

Bootstrap stage 5 prints commands like this for each point in the phase:

```
hermes kanban swarm --name "MyApp — PRD BUILD: Research" \
  --description "Build X" \
  --workdir "/path/to/project" \
  --max-workers 66 \
  --phase prd_build \
  --point research
```

Execute these commands in sequence (each point depends on the previous point's verifier + synthesizer). After all points complete, run the orchestration via `hermes chat -q "Load hermes-swarm-loop skill and continue phase 'X' for 'Y'"`.

## Auto Skill Update
After each phase completes, `skill_manage('patch')` is called to update SKILL.md with:
- Key findings from the phase
- New rules/patterns discovered
- Updated pitfalls
- Phase completion status

**Execution:** Read the current SKILL.md, identify the section to update (e.g. "Rules" or add "Phase N Completion"), write the new insights as a patch. Bump the version number in frontmatter.

## Runtime Behavior Notes

Real-world observations from running Phase 1-3 on the framework itself (dogfood, v6.5.0):

### Gateway Dispatch
- Gateway dispatches ready tasks on its internal tick (~60s interval). Workers transition from `ready` → `running` within one tick.
- `hermes kanban dispatch --max N` can trigger manual dispatch outside the tick cycle, but is rarely needed — the gateway handles it.
- Workers show as `ready` (queued for dispatch) before being picked up. If they stay `ready` for multiple minutes, the gateway may be at max concurrent children (configurable via `delegation.max_concurrent_children`, default 33 for this user).
- Blocked workers (after gateway restart or crash): `hermes kanban unblock <id> && hermes kanban dispatch --max 1` recovers them.

### Scratch Workspace Cleanup
- Each worker gets a scratch workspace at `~/.hermes/kanban/boards/<board>/workspaces/<task_id>/`.
- Scratch workspaces are **deleted automatically** when the task completes. Files written to the scratch workspace do NOT persist to the project directory.
- Workers that need to produce persistent output must write directly to the project workdir (e.g., `/opt/hermes-swarm-loop/engine/...`), not just to their workspace.
- Verifier and synthesizer workspaces are also ephemeral. Their output lives in the task body/comments and in files they write to the project directory.

### Agent Auto-Commit Behavior
- Code generation agents (Phase 1 Pt3) and setup agents (Phase 1 Pt2) **commit to git automatically** during execution. They call `git add` + `git commit` as part of their task.
- A typical Phase 1 run produces 4-5 commits: one per point (setup, code gen) plus fix commits from overlapping workers.
- Commits use descriptive messages like "Phase 1 Point 3: CODE GENERATION — 11 agents complete".
- The local git history accumulates commits; the final state is up-to-date with all generated code in-tree.
- This means: **do not manually commit Phase 1 output** — the agents handle it. Just push to GitHub after each phase.

### Verifier & Synthesizer Default Skills
- The `--verifier default` flag loads the `requesting-code-review` skill for the verifier agent.
- The `--synthesizer default` flag loads the `humanizer` skill for the synthesizer agent.
- Workers load `--skills kanban-worker --skills <project-skill>` (e.g., `hermes-swarm-loop`).
- If you override `--verifier` or `--synthesizer` with a custom profile, ensure that profile has the appropriate skills loaded.

### Blocked Worker Recovery
If a worker shows `blocked` status:
1. Check cause: `hermes kanban show <id>` — look for events/run history
2. Unblock: `hermes kanban unblock <id>`
3. **CRITICAL — Re-dispatch**: `hermes kanban dispatch --max 1`
   - `unblock` sets status to `ready`, NOT `running`. The gateway may NOT auto-dispatch a previously-blocked worker on its next tick — it treats `ready` from unblock differently than initial dispatch.
   - `dispatch --max 1` is **mandatory**, not optional. Without it, the worker sits in `ready` forever.
4. **"Spawned: 0" after dispatch is NOT an error.** If the gateway's internal tick fired between your `unblock` and `dispatch` calls, the worker transitions to `running` autonomously. `dispatch --max 1` then finds nothing ready to claim and reports "Spawned: 0". This is normal. Verify by checking the worker's status directly: `hermes kanban list --json | python3 -c "..."`.
5. Verify: `hermes kanban list --json | python3 -c "import json,sys; d=json.load(sys.stdin); t=next((x for x in d if x['id']=='TASK_ID'),None); print(t['status'] if t else '?')"` — should show `running` or `done`, not `ready` or `blocked`.
6. If it blocks again immediately, the agent may have crashed (bad skill load, token limit, etc.). You can `hermes kanban unblock <id>` + `dispatch` again with `--failure-limit 3` for auto-retry.

### Verifier/Synthesizer Wait Pattern After Workers Complete

After all 11 workers in a point complete, there is a **consistent 2-5 minute gap** before the verifier starts running, and another 1-3 minutes before the synthesizer completes:

| Event | Typical Delay After 11/11 Workers Done |
|-------|---------------------------------------|
| Workers → done (11/11) | 0 min (baseline) |
| Verifier transitions from `todo` → `ready` → `running` | +1-3 min |
| Verifier completes → `done` | +2-3 min |
| Synthesizer transitions from `todo` → `ready` → `running` | +0-2 min after verifier done |
| Synthesizer completes → `done` | +1-3 min |
| **Full point complete (14/14)** | **+4-8 min** |

The gateway does NOT start the verifier immediately when workers finish — it waits for its next tick cycle. Similarly, the synthesizer waits until the verifier is done, then gets dispatched on the next tick.

**Polling must account for this gap.** A poller that checks workers every 2 min but only waits 4 min (2 extra polls) for verifier+synthesizer will time out before they finish. Use a sweep poller with 60s intervals for the verifier/synthesizer check.

For individual task status, `hermes kanban show <task_id>` is more reliable than parsing `hermes kanban list --json` for a single task:

### Monitoring/Polling Pattern
The most reliable monitoring pattern for long-running swarms:

```bash
# Background poll every 2 minutes, notifies when all workers done
hermes kanban list --json 2>/dev/null | python3 -c "
import json,sys
data=json.load(sys.stdin)
workers=[t for t in data if 'Keyword' in t.get('title','')]
done=sum(1 for w in workers if w.get('status')=='done')
print(f'{done}/{len(workers)} workers done')
"
```

Key metrics per poll:
- Workers done = count of workers with status "done"
- Workers running = status "running"  
- Verifier status = "todo" (waiting), "running", or "done"
- Synthesizer status = same lifecycle
- Total done = count of all tasks with status "done" (should reach 14 per point: 1 root + 11 workers + 1 verifier + 1 synthesizer)

### Poller Script Pitfalls

**BUG: Stale `$data` capture in inner loop.** The most common polling error is capturing `$data=$(hermes kanban list --json 2>/dev/null)` once before the inner loop and reusing it to check verifier/synthesizer status. This gives EMPTY status output because the variable isn't refreshed. Always call `hermes kanban list` fresh inside every loop iteration:

```bash
# WRONG — stale $data in inner loop:
data=$(hermes kanban list --json 2>/dev/null)
# ... workers done check ...
for j in 1 2 3 4; do
  sleep 60
  # $data is STALE here!
  verifier_status=$(echo "$data" | python3 -c "...")
done

# CORRECT — refresh every iteration:
for j in 1 2 3 4; do
  sleep 60
  fresh_data=$(hermes kanban list --json 2>/dev/null)   # ← refresh!
  verifier_status=$(echo "$fresh_data" | python3 -c "...")
done
```

**Common workaround:** Use `hermes kanban show <task_id>` for a single task instead of parsing the full list — simpler and less error-prone.

### Sweep Poller for Straggler Workers

The main poller (12 × 120s = 24 min timeout) may time out while 1-2 workers are still blocked/running. After the main poller completes, run a **sweep poller** with tighter intervals (60s) and action on blocks:

```bash
# After main poller completes but not all workers done
for i in 1 2 3 4 5 6 7 8; do
  sleep 60
  data=$(hermes kanban list --json 2>/dev/null)
  # Check worker status
  workers=$(echo "$data" | python3 -c "
import json,sys
data=json.load(sys.stdin)
workers=[t for t in data if 'AgentKeyword' in t.get('title','')]
done=sum(1 for w in workers if w.get('status')=='done')
running=sum(1 for w in workers if w.get('status')=='running')
blocked=sum(1 for w in workers if w.get('status')=='blocked')
ready=sum(1 for w in workers if w.get('status')=='ready')
print(f'{done}/{running}/{blocked}/{ready}')
")
  # Auto-recover blocked workers
  blocked_ids=$(echo "$data" | python3 -c "
import json,sys
data=json.load(sys.stdin)
for t in data:
    if t.get('status')=='blocked' and 'AgentKeyword' in t.get('title',''):
        print(t['id'])
  ")
  for bid in $blocked_ids; do
    hermes kanban unblock "$bid"
    hermes kanban dispatch --max 1
  done
  if [ "$done" = "11" ]; then break; fi
done
```

The sweep poller handles the common pattern where 10/11 finish but the 11th is blocked. Unblock + dispatch brings it back, and the tighter 60s interval catches it quickly without wasting 2 min per check.

### Phase 1 Typical Output Metrics
From a dogfood run on the Hermes Swarm Loop framework itself:
- **Phase 1**: 3 points × 11 workers = 33 agents
- **Runtime**: ~45-75 minutes wall time (ARCH ~15min, SETUP ~30min, CODE ~30min)
- **Generated**: ~6,500 lines of Python across 23 files, 7 arch docs, 9 config files, 2 CI/CD files
- **Tests**: ~390 tests across 12 test files, all passing
- **Git commits**: 4-5 auto-commits from agents
- **File structure created**: engine/ (10 files), scaling/ (7 files), configs/ (9 files), arch/ (7 files), tests/ (12 files), .github/workflows/ (2 files), bootstrap.py, __main__.py, Makefile, pyproject.toml, requirements.txt

## Cycle Flow: Phase 2↔Phase 3 Swap Pattern (HUNT→QUALITY)

The Hermes Swarm Loop does NOT repeat all phases in subsequent cycles. The flow is:

```
Phase 1 (Development) ── runs ONCE
    └→ ARCH(11) → SETUP(11) → CODE(11)
          ↓
Phase 2 (Hunting) ── first pass (find bugs FIRST)
    └→ BUGS(11) → ARCH_REVIEW(11) → SECURITY(11)
          ↓
Phase 3 (Quality) ── then fix
    └→ AUDIT(11) → IMPROVE(11) → REVIEW(11)
          ↓
Mastery Gate ──→ PASS? → Done ✓
    |                |
    NO ←─────────────┘
    |
    Phase 2 (Hunting) ── re-run (NOT Phase 1)
    └→ BUGS(11) → ARCH_REVIEW(11) → SECURITY(11)
          ↓
    Phase 3 (Quality) ── re-run
    └→ AUDIT(11) → IMPROVE(11) → REVIEW(11)
          ↓
    Mastery Gate ──→ PASS? → Done ✓
         |              |
         NO ←───────────┘
         |
         ... repeat until PASS or BLOCK
```

**Key rules:**
- **Phase 1 runs EXACTLY ONCE.** Never re-run architecture/code generation.
- **Phase 2 (HUNTING) runs FIRST, then Phase 3 (QUALITY).** Bug finding before fixing — agents work on ground truth.
- **Phase 2 and Phase 3 alternate** (swap pattern). After Phase 3's gate, if NOT PASS, go back to Phase 2, NOT Phase 1 or Phase 3.
- **Mastery Gate at END of Phase 3 only** (not after Phase 2). Phase 3 includes audit and review — the gate evaluates the FULL output after bugs are found AND fixed.
- **On BLOCK (< 0.30):** abort the cycle. Do NOT loop. Report to user.
- **On CROSS-CHECK (0.50-0.69):** fix the specific gaps flagged by scoring agents, re-run gate only (skip full Phase 2/3 re-run).
- **On REVIEW (0.30-0.49):** abort like BLOCK — not acceptable to continue.
- **This is NOT "Cycle 2+: iterate".** The swap pattern is fundamentally different: it re-runs only Phase 2+3, never Phase 1, and alternates HUNT→QUALITY between them until the gate passes. The old "Cycle 2+: iterate" concept (re-running all phases including 1 with self-reflection) is retired in favor of this swap pattern.

### One-Cycle Mode (Edward's standard request)
When Edward says "one cycle" or "jeden cykl":
1. Run Phase 1 (ARCH + SETUP + CODE) = 33 agents
2. Run Phase 2 (BUGS + ARCH_REVIEW + SECURITY) = 33 agents — HUNT first
3. Run Phase 3 (AUDIT + IMPROVE + REVIEW) = 33 agents — then fix
4. Mastery Gate at end of Phase 3
5. If PASS → stop. If NOT PASS → loop Phase 2 (HUNT) → Phase 3 (FIX) → Gate → repeat
6. Max 999 agents total across ALL loops (not per cycle)
7. YOLO default ON throughout

This generates the code once, then hunts for real bugs first, and fixes based on ground truth in alternating loops until the gate passes.

### Multi-Loop Validation Mode (framework testing)
When Edward wants to validate the loop mechanism itself (e.g., "zrobić kilka cykli Phase 2-3"):
1. Run Phase 1 once (ARCH + SETUP + CODE) if not already done
2. Run 2-3+ full cycles of: Phase 2 (BUGS+ARCH+SECURITY = 33 agents — HUNT) → Phase 3 (AUDIT+IMPROVE+REVIEW = 33 agents — FIX) → Mastery Gate
3. Each Loop = 66 agents + 3 gate agents = ~69 agents per loop
4. Each Phase 2+3 loop = ~1.5-2 hours wall time
5. On each loop, give agents unique titles with suffix like "L2", "L3" to distinguish tasks
   - `--worker "default:Code Audit Agent L2:kanban-worker,hermes-swarm-loop"`
6. After each loop, push to GitHub before starting the next loop
7. On GATE PASS → start next loop anyway (Edward wants to test the loop)
8. On GATE BLOCK (< 0.30) → stop, report
9. Polling timeout must increase on later loops as code quality improves but fewer bugs remain (agents take longer to find issues)

**Key difference from production mode:** In validation mode, PASS does NOT terminate. Keep looping until Edward says stop or GATE BLOCK fires.

## Rules
- **Phase 1: BUILD** — always build from scratch, never re-run Phase 1
- **Phase 2+3: HUNT→FIX** — hunting (bugs/arch/security) ALWAYS runs before quality (audit/improve/review). Swap between these until Mastery Gate passes
- **Forced points** — every point runs, no skipping
- **Gate 11** — verifier must pass before next point (under Mastery Gate)
- **Auto-detect** — project size auto-determines agent count (11/33/66/999)
- **YOLO default ON** — auto-approve ALL actions. NEVER ask for permission, confirmation, or "co dalej". Only exception: after 999 agents dispatched, ask once.
- **Scale: 11→999** — no hard cap on agent count

## Execution Guide

Use `hermes kanban swarm` to run each point. The gateway dispatcher handles claiming and execution automatically.

### Pattern for Each Point (ARCH, SETUP, CODE GEN, etc.)
1. **Create swarm**: `hermes kanban swarm --worker "profile:title:skill" --verifier profile --synthesizer profile "goal" --json`
   - Exactly 11 workers per point. Each worker is one task.
   - Workers are independent `hermes chat -q "work kanban task t_xxx"` subprocesses.
   - Gateway dispatcher picks up ready tasks on its tick interval (default 60s).
   - Verifier runs after ALL 11 workers complete.
   - Synthesizer runs after verifier passes.

2. **Set up background monitoring** (recommended over foreground polling):
   ```bash
   hermes kanban list --json 2>/dev/null | python3 -c "
   import json,sys
   data=json.load(sys.stdin)
   workers=[t for t in data if 'YourAgentKeyword' in t.get('title','')]
   done=sum(1 for w in workers if w.get('status')=='done')
   running=sum(1 for w in workers if w.get('status')=='running')
   blocked=sum(1 for w in workers if w.get('status')=='blocked')
   print(f'Workers: {done}/{running}/{blocked} done/running/blocked')
   "
   ```
   For long runs, use a background process with `sleep 120` between polls.

3. **Wait for completion**: Workers → done (11/11), verifier → done, synthesizer → done = point complete (14/14 total tasks).

4. **Check outputs**: Workers should write to the project directory (NOT just their scratch workspace, which gets cleaned up). Check with `find . -newer SKILL.md -type f`. If no files found, check kanban task comments via `hermes kanban show <id>` for agent output.

5. **Auto Skill Update**: `skill_manage('patch')` with phase findings, rules, version bump.

6. **Mastery Gate**: Spawn 1-3 cross-check agents via `delegate_task`. Each agent evaluates a non-local PRD area. Score 7 dimensions, average, compare to thresholds. Fix CROSS-CHECK gaps; abort on BLOCK.

7. **GitHub Push**: Use the `gh api` blob→tree→commit→ref pipeline (`python3` script building tree JSON → `gh api .../git/trees --input ...`). The agents auto-commit to git during execution, so the local repo is already up-to-date. Push all 63+ files including engine/, scaling/, configs/, arch/, tests/, .github/.

8. **Next point/phase**: On Mastery Gate PASS, proceed. On CROSS-CHECK, fix gaps and re-gate. On BLOCK, re-run the phase.

## Known Project Locations

The Hermes Swarm Loop framework lives in two locations on this VPS:

| Path | Status | Content |
|------|--------|---------|
| `/root/code/hermes-swarm-loop/` | **Canonical / Active** | Full v6.x with engine/, scaling/, tests/, configs/, arch/ |
| `/opt/hermes-swarm-loop/` | Archive | v5.0.0 base (PRD, docs, launch scripts only — no engine/scaling) |

**Always work in `/root/code/hermes-swarm-loop/`** unless Edward explicitly says otherwise. The `/opt/` copy lacks all generated code (engine, scaling, tests, configs, arch). If you start a dogfood run on `/opt/`, you are rebuilding from scratch, not enhancing the existing framework.

## Disaster Recovery (Project Code Wiped)

If the VPS is rebuilt and `~/code/hermes-swarm-loop/` is gone but the skill survives:

1. **Clone the repo**: `git clone https://github.com/DominikKrawczyk/hermes-swarm-loop.git ~/code/hermes-swarm-loop`
2. **Verify DB presence**: GitHub repo has `.swarm_state.db`? No — DB is local-only and ephemeral. Run `python3 bootstrap.py --project-name "..." --project-desc "..." --init-only` to recreate it.
3. **Recreate scaling modules if missing**: If the repo only has the old archive (v2.0.0) and the modern `engine/` and `scaling/` directories are absent, use `delegate_task` with parallel subagents to rebuild them. This session reconstructed 10+ modules (4,585 lines) in parallel — 3 minutes wall time. Pattern:
   - Load the 12 reference files via `skill_view(name='hermes-swarm-loop', file_path='references/...')` for all of them
   - Spawn 8-10 parallel subagents, each building one module from the reference specs
   - Verify with `python3 -m pytest tests/test_all.py -v`
4. **Push back to GitHub immediately**: Run the `gh api` blob→tree→commit→ref pipeline (see `references/github-push-pipeline.md`) to lock in the recovery, so the VPS wipe can only happen once.

### Critical Rules
1. **FIRST check all known paths before rebuilding.** The canonical working copy lives at `/root/code/hermes-swarm-loop/`. There is also an archive copy at `/opt/hermes-swarm-loop/` (v5.0.0 base, no engine/scaling). Run `find /root/code /opt /root -maxdepth 4 -type d -name "hermes-swarm-loop"` before declaring anything missing. The skill file survives at `~/.hermes/skills/hermes-swarm-loop/` regardless of VPS state. NEVER assume data is gone without exhaustive search. NEVER `rm -rf` any directory matching a user's project name without explicit confirmation.
- **SQLite row-to-dataclass must include `id` field.** Every SQLite table has `id INTEGER PRIMARY KEY`, but dataclasses like `PhaseEntry`, `PointEntry`, and `YOLOState` will raise `TypeError: __init__() got an unexpected keyword argument 'id'` if you unpack `**dict(row)` without an `id` field. Always add `id: int = 0` (or `id: int = 1` for singleton tables like `yolo_state`) to dataclasses that mirror DB rows.
- **SQLite transaction context manager must yield `cursor`, not `connection`.** Python's `sqlite3.Connection.execute()` returns a `Cursor`, but `connection.rowcount` does not exist — only `Cursor.rowcount` does. If a state machine's `update_with_cas` uses `c.execute(...)` and checks `c.rowcount`, and the context manager yields `self.conn`, it raises `AttributeError: 'Connection' object has no attribute 'rowcount'`. Fix: `@contextmanager: with self._lock: c = self.conn.cursor(); yield c; self.conn.commit()`. Always test that the CAS guard actually raises `ConflictError` on version mismatch, not just that it executes without error.
- **PointMachine lifecycle: create_point → todo, start_point → running, complete_point/fail_point → done/failed.** `create_point` sets status to `todo` (not `running`). Tests that assume `create_point` creates in `running` will fail on `complete_point` or `fail_point`. The correct sequence is: `create_point(...)` → `start_point(...)` → `complete_point(...)`/`fail_point(...)`. This affected ~8 tests during the Phase 1 state machine refactor — fix by adding `start_point` calls between create and complete/fail.
- **11 PER POINT, not 11 total.** A phase with 3 points = 33 agents (3 × 11). Each point is a separate `hermes kanban swarm` call. Never combine all 3 points into one swarm.
- **NEVER use `delegate_task` for multi-agent spawning.** Use `hermes kanban swarm`. delegate_task is only for Mastery Gate cross-check agents (1-3 agents), never for phase workers.
- **NEVER `rm -rf` any directory without explicit user confirmation.** `rm -rf ~/code/hermes-swarm-loop` destroyed the working framework during one session. The framework repo lives at BOTH `/root/code/hermes-swarm-loop/` (active/current) AND `/opt/hermes-swarm-loop/` (v5.0.0 archive). The `/root/code/` copy is the canonical one with full engine/scaling/tests. Always check both paths before concluding the framework is gone: `find /root/code /opt -maxdepth 3 -name "hermes-swarm-loop" -type d`. Never delete anything that matches a user's project name.
- **NEVER ask for permission.** YOLO is default ON. The ONLY time to ask "co dalej" is after 999 agents have been dispatched. Everything else proceeds automatically — no questions, no confirmations, no "shall I proceed".
- **Gateway dispatcher runs automatically** — do NOT manually `hermes kanban claim` or `hermes kanban daemon`. The embedded gateway dispatcher handles this.
- **After gateway restart**, workers may show "blocked" status. Fix: `hermes kanban unblock <id>` then `hermes kanban dispatch`.
- **Phase 0** (PRD BUILD, 66 agents): can use delegate_task for initial research+build, or split into 2 kanban swarms (33 research + 33 build). Phase 1+ must use kanban swarm.
- **Agents auto-commit to git.** Do not manually commit Phase 1-3 output. The workers call `git add` + `git commit` as part of their task. Just push to GitHub after each phase.
- **Workers write to scratch workspaces that get auto-cleaned.** If workers should produce persistent files, the task goal must explicitly say "write to /project/dir/...". Scratch output is lost when the task completes.
- **Verifier loads `requesting-code-review` skill; synthesizer loads `humanizer` skill.** These are defaults from `--verifier default` / `--synthesizer default`. Workers load `--skills kanban-worker --skills <project-skill>`.

### Phase 2 Bug Hunting (v6.7.0 — 2026-06-02)

Phase 2 Point 1: 11 bug hunting agents scanned all 34 source files. **15 bugs found & fixed, 376/376 tests pass.**

### Phase 2 Architecture Review (v6.7.0 — 2026-06-02)

Phase 2 Point 2: 11 architecture review agents produced a **338-line report** identifying **13 architecture-to-code inconsistencies** including:

### Phase 2 Security Audit (v6.7.0 — 2026-06-02)

Phase 2 Point 3: 11 security audit agents produced a **541-line report** covering 32 source files (~3,400 lines). Results:
- 7 scaling modules (1,340 lines) completely unwired despite arch showing integration flow

**Key lesson:** Architecture documents written pre-implementation (v6.4.0) are dangerously misleading for post-implementation (v6.5.1) readers. Docs must be updated after code generation or labeled as "pre-implementation plan, not accurate reference."

### Phase 3 Security Audit (v6.7.0 — 2026-06-02)

Phase 3 Point 3: 11 security audit agents produced a **541-line report** covering 32 source files (~3,400 lines). Results:
- **0 critical** vulnerabilities
- **1 high** (S1: COALESCE bug in start_phase() — allows done-phase restart, blocks failed-phase restart; flagged as B1/CRITICAL in bug hunt but fix never applied to this repo)
- **2 medium** (S4: subprocess argument injection; S5: PriorityQueue.size lock protection — note: S5 may be a false positive, actual code has `with self._lock:`)
- **5 low** findings (mixed permissions, TOCTOU in CLI, Rich markup injection, etc.)
- All scaling modules (1,340 lines across 7 files) confirmed clean — no exploitable vulnerabilities, well-tested, thread-safe, but **completely unwired from runtime**
- CAS versioning: CORRECT on all 12 mutation methods
- No SQL injection, command injection, embedded secrets, unsafe eval/exec, or pickle deserialization found

### Dogfood Run v6.7.0 — Full Phase 1-3 + Mastery Gate Results (old order: Quality→Hunting)

A complete dogfood run of the Hermes Swarm Loop framework on itself at /opt/hermes-swarm-loop/:

| Stage | Agents | Runtime | Result |
|-------|--------|---------|--------|
| Phase 1: ARCH | 11 | ~15 min | 7 arch docs |
| Phase 1: SETUP | 11 | ~30 min | 34 files, bootstrap.py |
| Phase 1: CODE | 11 | ~30 min | 6,503 lines, 390 tests |
| Phase 2: BUGS | 11 | ~25 min | 15 bugs found & fixed |
| Phase 2: ARCH | 11 | ~10 min | 13 arch-to-code inconsistencies |
| Phase 2: SECURITY | 11 | ~10 min | 0 critical, 1 high, 2 med, 5 low |
| Phase 3: AUDIT | 11 | ~20 min | 7 bugs found |
| Phase 3: IMPROVE | 11 | ~20 min | 7 bugs fixed |
| Phase 3: REVIEW | 11 | ~15 min | 390/390 pass |
| **Mastery Gate** | **3 cross-check** | **~3 min** | **PASS (0.7118)** |

**Total: 99 agents + 3 gate agents = 102 agent runs, 126 kanban tasks, ~2.5 hours wall time.**

**Blocked worker rate:** ~10% across all phases (consistent with v6.6.0). All recovered via `hermes kanban unblock <id> && hermes kanban dispatch --max 1`.

**Mastery Gate scores breakdown:**
| Dimension | Avg Score | Weight |
|-----------|-----------|--------|
| correctness | 0.7633 | 0.25 |
| safety | 0.7200 | 0.20 |
| test_coverage | 0.7933 | 0.15 |
| consistency | 0.5633 | 0.15 |
| diversity | 0.6333 | 0.10 |
| efficiency | 0.7267 | 0.10 |
| clarity | 0.7500 | 0.05 |
| **Weighted total** | **0.7118** | **1.00** |

**Key gaps (flagged by 2+ gate agents but within PASS threshold):**
1. COALESCE bug (S1/B1) still unfixed — start_phase() allows done-phase restart, blocks failed-phase restart
2. Architecture docs are stale — v6.4.0 pre-implementation specs vs v6.5.1 actual code
3. 1,340 lines of scaling modules unwired from runtime
4. CLI has 0% test coverage (334 lines)
5. N+1 query pattern in state machine mutations

| ID | Severity | File | Issue |
|----|----------|------|-------|
| B1 | CRITICAL | `state_machine.py` | COALESCE prevented failed-phase restart, allowed done-phase restart |
| B2 | CRITICAL | `mastery_gate.py` | Only 3/7 dims checked in `check_diversification()` |
| B3 | MEDIUM | `connection_pool.py` | `_waits` phantom increment on immediate timeout |
| B4 | MEDIUM | `connection_pool.py` | Properties not locked (race condition) |
| B5 | MEDIUM | `priority_queue.py` | `size` property not locked |
| B6 | LOW | `connection_pool.py` | `close_all()` leaked in-use connections |
| B7 | LOW | `circuit_breaker.py` | HALF_OPEN allowed unlimited concurrent probes |
| B8 | LOW | `configs/config.yaml` | Version mismatch (6.4.0 vs 6.5.1) |
| B9 | LOW | `cas_store.py` | Dead `ConflictError` class never used |
| B10 | MEDIUM | `bootstrap.py` | YOLO zone cap bypassed in `create_point` — used uncapped `args.max_agents` |
| B11 | LOW | `cli.py` | 10 unused imports from initial scaffolding |
| B12 | LOW | `state_machine.py` | PEP 484 type annotation in `log_event` |
| B13 | LOW | `mastery_gate.py` | 10+ PEP 8 compound statement violations |
| B14 | ADVISORY | `queue_pressure.py` | Unused `field` import |
| B15 | ADVISORY | `cli.py` | Workspace CLI uses isolated WM instances |

**New rules added to Critical Rules:**
- `start_phase` must use explicit status guard with `if status in ("done", "failed", "archived", "blocked"): raise ConflictError(...)` — the COALESCE approach has confusing edge cases.
- `check_diversification()` must check ALL 7 dimensions, not just 3 hardcoded ones. Use a loop over `DIMENSIONS`.
- Connection pool properties (`size`, `idle`, `in_use`, `available`, `active`) must acquire `self._lock` internally.
- Priority queue `size` property must be lock-protected.
- CircuitBreaker HALF_OPEN must enforce exactly 1 concurrent probe.
- `bootstrap.py` must pass `capped` (not `args.max_agents`) to `create_point` after YOLO zone cap is applied.
- `close_all()` must call `_discard_internal()` on in-use connections, not just idle ones.

## Dogfood Results (v6.5.0 — 2026-06-02)

Framework proven on itself through a fresh Phase 1 run (Cycle 1 BUILD, no iteration):

- **Phase 1**: 3 kanban swarms × 11 workers (33 total) + 3 verifiers + 3 synthesizers = 42 total tasks
- **Phase 1 Runtime**: ~45-75 minutes wall time (ARCH ~15min, SETUP ~30min, CODE ~30min)
- **Generated**: 6,503 lines of Python across 23 files, 7 arch docs (69KB total), 9 config YAMLs, 2 CI/CD workflows
- **Test suite**: 390 tests across 12 test files — **390/390 passed**
- **Git commits**: 4 auto-commits from agents during Phase 1 Pt2 and Pt3
- **File structure created**:
  - `engine/` — state_machine (456L), cli (655L), workspace_manager (332L), agent_roles, gate_11, gate_verifier, mastery_gate, synthesizer, config, __init__
  - `scaling/` — token_bucket, adaptive_batcher, circuit_breaker, connection_pool, priority_queue, queue_pressure, cas_store
  - `configs/` — agent_roles, config, engine_config, logging_config, mastery_gate_config, sample_config, scaling_config, swarm_config, workspace_config, yolo_config
  - `arch/` — agent-roles, architecture-overview, mastery-gate-spec, scaling-infrastructure, state-machine-architecture, workspace-manager-spec, yolo-zones
  - `tests/` — 12 test files (state_machine, scaling, workspace_manager, integration, bootstrap, gate_11, gate_verifier, mastery_gate, synthesizer, agent_roles, config, conftest)
  - `.github/workflows/` — ci.yml, test.yml
  - Root: bootstrap.py, __main__.py, Makefile, pyproject.toml, requirements.txt
- **Mastery Gate**: PASS (0.878) — verified by non-local security cross-check via delegate_task
- **Security audit**: No critical vulnerabilities found. 1 medium gap (optimistic CAS version not validated with WHERE clause). 6 low/info findings.
- **GitHub push**: 63 blobs pushed via `gh api` pipeline

### Comparison to v6.2.0
The v6.2.0 dogfood run produced ~31K lines across 77 dirs (9.4MB). The v6.5.0 run produced 6.5K lines across 23 files — smaller because:
- The agents wrote focused implementations rather than generating multiple variants
- The code generation agents enhanced files created by setup agents (overwrite, not append)
- The arch docs were 7 consolidated documents rather than 30+ individual ones
- Some generated code (agent roles infra, 198 roles) was represented as config rather than expanded code

### Phase 3 Quality Run (v6.6.0+, renumbered from old Phase 2)

Phase 3 run on itself (dogfood, same session as v6.5.0 Phase 1):

| Point | Workers | Runtime (per point) | Notes |
|-------|---------|---------------------|-------|
| AUDIT | 11 | ~15-20 min | Workers complete in 5-15 min each |
| IMPROVE | 11 | **~25-35 min** | Workers take 15-25 min each — they READ code, MAKE changes, RUN tests, and COMMIT. This is the slowest point in any loop. |
| REVIEW | 11 | ~15-20 min | Workers complete in 5-15 min each |

**Block rate:** ~12% (4 blocked out of 33 workers across Phase 2). Blocks were transient (agent crash, token limit). All recovered via `hermes kanban unblock <id> && hermes kanban dispatch --max 1`. No worker needed more than 1 retry.

**Verifier timing:** ~2-3 minutes per verifier. Synthesizer: ~1-2 minutes. The whole Phase 2 (3 points × 14 tasks = 42 total) completed in ~75-90 minutes wall time.

**Blocked worker recovery was needed in EVERY Phase 2 point.** Always check for blocked workers after the main 11 complete. Pattern:
```bash
hermes kanban list --json | python3 -c "
import json,sys
data=json.load(sys.stdin)
for t in data:
    if t.get('status')=='blocked':
        print(f'BLOCKED {t[\"id\"]}: {t.get(\"title\",\"?\")}')
"
# Then for each:
hermes kanban unblock <id>
hermes kanban dispatch --max 1
```

Phase 2 Point 1: 11 code audit agents scanned engine/, scaling/, configs/, tests/, bootstrap.py, __main__.py, Makefile (~6,500 lines, 23 source files). Results:

**Bugs found & fixed (3):**
1. **CAS bug** — 12 mutation methods in state_machine.py incremented `version=version+1` without `WHERE version=?`. All fixed with proper SELECT-version-then-UPDATE-WHERE-version=? pattern.
2. **Config dict mutation** — `_deep_merge` shallow copy corrupted default configs. Fixed with `copy.deepcopy`.
3. **Synthesizer dedup count** — fragile `len()` on mixed list/dict outputs. Fixed with `_count_items()` helper.

**Key new rules (added to Critical Rules):**
- ALL UPDATE operations with `version=version+1` must include `WHERE version=?` with a prior SELECT
- INSERT ON CONFLICT (upsert) must split into separate INSERT vs UPDATE branches for proper CAS
- `_deep_merge` MUST use `copy.deepcopy` not shallow `copy()`
- Synthesizer dedup count must handle both list and dict outputs

**Test suite:** 390/390 pass (all fixes verified).

### Phase 1 Code Output
~31K lines, 77 dirs, 9.4MB: bootstrap.py (5-stage launcher: env check → DB init → phase setup → YOLO init → launch), state machine engine (3 machines: phase/point/YOLO, SQLite-backed with WAL + CAS), Mastery Gate engine (7-dim scoring), Gate 11 verifier, scalability infra (7 modules: token bucket, adaptive batcher, CAS store, circuit breaker, connection pool, priority queue, queue pressure), workspace management (scratch/dir/worktree), YOLO config (4 zones + safety valve), agent role infra (198 roles), test suite, 30+ arch docs.

### Key Lessons
- Each scaling module needs a config section in scaling_config.yaml
- State machine transitions: idempotency guard + event audit log
- CAS store must init before any workspace operation
- Shell for orchestration, Python for logic
- Gate 11 verifier expects JSON-schema handoffs; validate before verify
- WAL mode + write lock for concurrent state machine access
- **ALL mutation methods in state_machine.py MUST include `WHERE version=?` on every UPDATE.** Version is incremented atomically in SQLite, but without checking the current version, the optimistic CAS pattern is broken — concurrent writers can silently overwrite. Every `UPDATE ... SET version=version+1` needs a `SELECT version` first, then `WHERE version=?` to validate the expected version.
- **INSERT ON CONFLICT (upsert) must split into separate INSERT vs UPDATE branches for proper CAS.** The old pattern `ON CONFLICT DO UPDATE SET version=version+1` incremented the version without any version check. Split into: (1) `SELECT version`, (2) if exists: `UPDATE ... WHERE version=?`, (3) if not: `INSERT`.
- **`_deep_merge` must use `copy.deepcopy` not shallow `copy()`.** Shallow copy shares nested dict references, causing silent mutation of input dicts (e.g., module-level DEFAULT_CONFIG dicts corrupted after one merge call).
- **Synthesizer dedup count must handle dict outputs.** `len(output)` on a dict returns key count, not item count. Use a helper that checks `isinstance(output, list)` vs `isinstance(output, dict)` with `output.get("findings", [])`.
- **CircuitBreaker `state` property must acquire `self._lock` before calling `_check_timeout()`** — the convenience properties (`is_open`, `is_closed`, `is_half_open`) delegate to `.state`, so they must all be lock-safe.
- **CircuitBreaker HALF_OPEN must enforce exactly 1 concurrent probe.** Add `_half_open_probe_in_flight` flag set in `_transition(HALF_OPEN)` and checked in `allows_request()`. Clear in `record_success()`/`record_failure()`.
- **AdaptiveBatcher `record_latency()` must acquire `self._lock`** before reading/writing `batch_size` — races with `set_batch_size()`, `add()`, and `flush()` which are all lock-protected.
- **ConnectionPool `max_connections.setter` must acquire `self._lock`** before writing `max_size` — races with `acquire()` which reads `max_size` inside its lock.
- **Synthesizer must guard against non-dict agent output** — `isinstance(output, dict)` check before calling `.get("findings", [])`. Strings and None crash otherwise.
- **TOCTOU in `increment_errors()`** threshold check must be inside the cursor context. Inline safety valve activation to avoid lock deadlocks on `threading.Lock`.
- **Shared-workspace agent coexistence** causes silent file corruption (duplicated lines, mangled indentation) when multiple workers edit the same files in parallel. Workers should verify their patches persisted, or use write_file to atomically replace entire files.
