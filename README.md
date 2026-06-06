# 🐝 Hermes Swarm Loop — 5-Phase Autonomous Build Framework

**Build anything — from zero to production-ready — with structured phases, parallel agent swarms (11→999), and iterative quality loops.**

Inspired by Ralph (19.8k⭐) × Ralphy (2.9k⭐) × ARIS (11.2k⭐) × Hive (10.5k⭐)

> **Repo:** `github.com/DominikKrawczyk/hermes-swarm-loop`  
> **Version:** 6.5.1  
> **License:** MIT  
> **Python:** 3.10+  
> **Author:** Edward Puszczyk (edward@puszczyk.dev)

---

## 📊 Codebase at a Glance

| Metric | Value |
|--------|-------|
| **Engine** | **10 modules**, 2,591 LOC — state machine, CLI, orchestrator, gates, workspace mgmt, git push, synthesizer, agent roles, config, bootstrap |
| **Scaling** | **7 infrastructure modules**, 1,429 LOC — connection pool, circuit breaker, token bucket, adaptive batcher, priority queue, CAS store, queue pressure |
| **Tests** | **375+ tests, 4,163 LOC** across 12 test files — 100% coverage of engine + scaling |
| **Architecture Docs** | **23 files**, 5,115 LOC — full spec for every component |
| **CLI Commands** | **15 commands** across 6 groups (phase, point, yolo, gate, workspace, swarm, config) |
| **Agent Roles** | **198 roles** defined across 5 phases — prd_build (66), development (33), hunting (33), quality (33), simplicity (33) |
| **State Machine** | **3 machines** sharing 1 SQLite DB with WAL mode + optimistic CAS |
| **YOLO Zones** | 4 escalation levels — safe → test → staging → production |
| **Total Python** | **8,523 LOC** (active source + tests) |

---

## 🔥 Quick Start

```bash
# Clone — works immediately, tests pass out of the box
git clone https://github.com/DominikKrawczyk/hermes-swarm-loop.git
cd hermes-swarm-loop
python3 -m pytest tests/    # 375+ tests ✅

# === PHASE 0: PRD BUILD ===
# 66 build agents: research + web search + precision questions + full PRD
python3 bootstrap.py \
  --project-name "MyApp" \
  --project-desc "description" \
  --phase prd_build \
  --yolo-zone staging \
  --max-agents 66

# === PHASE 1: DEVELOPMENT ===
python3 bootstrap.py \
  --project-name "MyApp" \
  --phase development \
  --yolo-zone test \
  --max-agents 33

# === FULL CYCLE (Phase 0→1→2→3→Gate→Loop) ===
python3 bootstrap.py \
  --project-name "MyApp" \
  --project-desc "..." \
  --yolo-zone staging \
  --max-agents 999
```

### Or as a library (Hermes Agent calls these):

```python
from engine.orchestrator import bootstrap_swarm, check_point_done, recover_blocked_workers
from engine.git_push import git_push_repo

# Bootstrap a phase
config = bootstrap_swarm("UltraSales", "Build marketing OS", "/opt/email-platform")

# Check if all agents finished
done = check_point_previous_state("/opt/email-platform")
recover_blocked_workers("/opt/email-platform")

# Push to GitHub
git_push_repo("/opt/email-platform", "Auto-update: Phase dev complete")
```

---

## 🧠 Architecture

### Core Loop

```
Phase 0: PRD BUILD — 66 agents (all build — research + questions + PRD)
     ↓
Phase 1: DEVELOPMENT — ARCH (11) → SETUP (11) → CODE (11)
     ↓
Phase 2: HUNTING — BUGS (11) → ARCH REVIEW (11) → SECURITY (11)   ← RUNS FIRST
     ↓
Phase 3: QUALITY — AUDIT (11) → IMPROVE (11) → REVIEW (11)        ← THEN FIX
     ↓
Mastery Gate ─────────── PASS? ──→ Done ✓
     ↓ NO
Phase 2 → Phase 3 → Gate → ... (loop until PASS)
```

### Phase Structure

| Phase | Points | Agents/Point | Total Agents |
|-------|--------|-------------|--------------|
| **Phase 0 — PRD BUILD** | build | 66 | 66 |
| **Phase 1 — Development** | architecture, setup, code_generation | 11 each | 33 |
| **Phase 2 — Hunting** | bugs, architecture_review, security | 11 each | 33 |
| **Phase 3 — Quality** | audit, improve, review | 11 each | 33 |
| **Simplicity** | 33 domains | 1 each | 33 |

### Agent Role Distribution — 198 Roles

Each agent is assigned a domain from 33 domains (state_machine, mastery_gate, scaling, workspace_management, yolo_zones, agent_roles, bootstrap, testing, ci_cd, logging, config_management, error_handling, concurrency, data_model, api_design, cli, documentation, security, performance, observability, recovery, orchestration, communication, storage, network, deployment, monitoring, quality_gates, feedback_loops, self_reflection, versioning, migration, compatibility).

Domains cycle across agents to ensure maximum diversity within each point.

---

## 🔥 Deep Features Breakdown

### 1. Engine Layer (`engine/`) — 10 Modules, 2,591 LOC

#### 1.1 State Machine (`state_machine.py` — 553 LOC)

**Three machines, one SQLite database** with WAL mode + optimistic CAS locking:

| Machine | Tracks | Key Transitions | Conflict Strategy |
|---------|--------|-----------------|-------------------|
| **`PhaseMachine`** | Phase lifecycle | `todo → running → done` | Version check on every write |
| **`PointMachine`** | Point lifecycle + agent count | `todo → running → done/blocked` | CAS + retry |
| **`YOLOMachine`** | YOLO zone + safety valve | `zone change, error count, valve` | Thread-safe with lock |

**`StateDB`** (SQLite-backed):
- **5 tables**: `phase_state`, `point_state`, `yolo_state`, `state_audit_log`
- **WAL mode** for concurrent reads/writes
- **Optimistic CAS** — every write checks `version` column, raises `ConflictError` on mismatch
- **Thread-safe** — per-thread connections via `check_same_thread=False`
- **Audit events** — all transitions logged to `state_audit_log`

**Features:**
- Idempotent transitions (safe to retry)
- Concurrent-safe with zero external locking
- Auto-schema creation on first use
- Full audit trail of all state changes

#### 1.2 Unified CLI (`cli.py` — 666 LOC)

**15 click commands** across 6 groups, installed as `hsl` console script:

| Group | Commands | Description |
|-------|----------|-------------|
| **`hsl phase`** | `start`, `complete`, `list`, `show` | Phase lifecycle |
| **`hsl point`** | `create`, `complete`, `list`, `show` | Point lifecycle |
| **`hsl yolo`** | `set`, `status`, `list`, `error`, `reset`, `activate-valve` | YOLO zone management |
| **`hsl gate`** | `evaluate`, `dimensions` | Mastery gate scoring |
| **`hsl workspace`** | `create`, `list` | Workspace management |
| **`hsl swarm`** | `status` | Comprehensive overview |
| **`hsl config`** | `show` | Inspect merged config |

**Built with:**
- `rich` — colored tables, panels, formatted output
- `click` — nested command groups, auto-help
- Auto-import resolves package vs source installs
- Config resolution: YAML with JSON fallback (3 search paths)

#### 1.3 Orchestrator (`orchestrator.py` — 257 LOC)

**Hermes-as-Orchestrator** — convenience functions for the LLM agent to drive the pipeline:

| Function | Purpose |
|----------|---------|
| `bootstrap_swarm()` | Run bootstrap.py to generate kanban tasks + launch config |
| `check_point_done()` | Verify all agents in a point completed |
| `check_point_previous_state()` | Check state of previous point before advancing |
| `recover_blocked_workers()` | Recover blocked agents (max 5 retries) |
| `swarm_status()` | Get comprehensive status report |

**Features:**
- Reads `.hermes_swarm_launch.json` from bootstrap output
- Point completion detection by counting kanban `done` tasks
- Blocked worker recovery with `delegate_task` re-dispatch
- Status reporting on phases, points, YOLO zone, and agent counts

#### 1.4 Mastery Gate (`mastery_gate.py` — 98 LOC)

**7-dimension quality scoring gate** that determines if a phase passes or loops back:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Correctness** | 0.25 | Code works correctly |
| **Safety** | 0.20 | No destructive or unsafe operations |
| **Test Coverage** | 0.15 | Tests cover the changes |
| **Consistency** | 0.15 | Consistent with existing code style |
| **Diversity** | 0.10 | Diverse range of changes |
| **Efficiency** | 0.10 | Efficient implementation |
| **Clarity** | 0.05 | Clear, readable code |

**Verdict thresholds:**
- **PASS** ≥ 0.70 → Phase complete, advance to next
- **CROSS-CHECK** ≥ 0.50 → Needs human review
- **REVIEW** ≥ 0.30 → Major issues found
- **BLOCK** < 0.30 → Completely failed, re-do phase

**`ScoreCard`** — per-agent score dataclass with weighted total calculation
**`MasteryGate`** — aggregate evaluation with diversification checks across 7 PRD areas

#### 1.5 Gate 11 Verifier (`gate_11.py` — 132 LOC)

**11-agent handoff verification** — ensures ALL agents in a point completed before advancing:

| Feature | Description |
|---------|-------------|
| **```Gate11Verifier```** | Verifies 11-agent completion |
| **`MINIMUM_HANDOFF_FIELDS`** | Required fields: `summary`, `worker_id`, `point`, `phase` |
| **`HandoffValidation`** | Per-agent validation result |
| **`GateResult`** | Aggregate result with `all_done`, `passed` flags |
| **JSON Schema** | Validates handoff JSON from every worker |

Ensures: `completed_agents == total_agents` AND all handoffs pass schema validation.

#### 1.6 Workspace Manager (`workspace_manager.py` — 347 LOC)

**3 workspace flavours** for kanban workers:

| Kind | Lifecycle | Use Case |
|------|-----------|----------|
| **`scratch`** | Temp directory per task, GC'd on archive | One-off agent work |
| **`dir`** | Shared persistent directory | Multi-agent shared output |
| **`worktree`** | Git worktree on feature branch | Branch-based development |

**Features:**
- Thread-safe registry with `setup()` / `teardown()`
- Automatic GC of scratch workspaces on task archive
- Git worktree with branch creation
- Observable: `active_count`, `list_active()`

#### 1.7 GitHub Push Pipeline (`git_push.py` — 156 LOC)

**Full GitHub API push** without git CLI subprocess:

| Function | Purpose |
|----------|---------|
| `git_push_repo()` | Push repo to GitHub via API (blob→tree→commit→ref) |
| `_resolve_remote_auth()` | Embed auth token in remote URL |
| `_get_gh_token()` | Extract token from `~/.config/gh/hosts.yml` |

**Auth resolution:**
1. Check if remote URL already has credentials
2. Try `~/.config/gh/hosts.yml` oauth_token
3. Embed token as `https://user:token@github.com/...`

**Commit strategy:**
- Prefers agents' own commits when present
- Falls back to phase-level auto-commit message

#### 1.8 Output Synthesizer (`synthesizer.py` — 104 LOC)

**Merge parallel agent outputs** into a single coherent artifact:

| Feature | Description |
|---------|-------------|
| **Merge Strategy** | `dedup_append` — content-hash deduplication |
| **Output Format** | JSON with merged findings |
| **Error Handling** | Failed agents tracked separately |
| **Timestamps** | ISO-format synthesis timestamp |

#### 1.9 Agent Roles (`agent_roles.py` — 108 LOC)

**198 agent role definitions** organized by phase:

```python
AGENT_ROLES = {
    "prd_build": [...]       # 66 agents, kind="build"
    "development": [...]     # 33 agents (11 arch + 11 setup + 11 code)
    "hunting": [...]         # 33 agents (11 bugs + 11 arch review + 11 security)
    "quality": [...]         # 33 agents (11 audit + 11 improve + 11 review)
    "simplicity": [...]      # 33 agents
}
```

Each agent: `{name, kind, domain, description}` — domain cycles through 33 domains.

#### 1.10 Bootstrap Launcher (`bootstrap.py` — 179 LOC)

**5-stage pipeline launcher:**

| Stage | Action | Description |
|-------|--------|-------------|
| 1 | **Environment Check** | Verifies hermes, python3, gh, git on PATH |
| 2 | **Database Init** | Creates `.swarm_state.db` with WAL + 5 tables |
| 3 | **Phase Setup** | Writes phase + point records to DB |
| 4 | **YOLO Init** | Configures YOLO zone and parallel agent caps |
| 5 | **Launch** | Prints kanban swarm commands, saves config to `.hermes_swarm_launch.json` |

**CLI flags:**
- `--project-name`, `--project-desc`, `--project-dir` — project metadata
- `--phase` — Phase 0/1/2/3 selection
- `--yolo-zone` — Escalation level (safe/test/staging/production)
- `--max-agents` — Agent count (11-999)
- `--websearch` — Add web search capability to agent goals
- `--git-push` — Auto-push to GitHub after bootstrap
- `--init-only` — Database init without launching agents

---

### 2. Scaling Infrastructure (`scaling/`) — 7 Modules, 1,429 LOC

#### 2.1 Circuit Breaker (`circuit_breaker.py` — 228 LOC)

**State machine pattern** for failure isolation:

```
CLOSED ──(N failures)──→ OPEN ──(timeout)──→ HALF_OPEN ──(N successes)──→ CLOSED
                                                              ↓ (1 failure)
                                                           OPEN
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `failure_threshold` | 5 | Consecutive failures before OPEN |
| `recovery_timeout` | 30s | Wait before HALF_OPEN |
| `consecutive_successes_to_close` | 1 | Successes needed to recover |

**Features:** Thread-safe via Lock, state callbacks, `CircuitBreakerOpenError` exception.

#### 2.2 Connection Pool (`connection_pool.py` — 352 LOC)

**Thread-safe connection pooling** for infrastructure resources:

| Feature | Value |
|---------|-------|
| **Min connections** | Configurable (default 2) |
| **Max connections** | Configurable (default 10) |
| **Idle timeout** | Reclaims stale connections |
| **Stats** | Active, idle, wait, total_created, total_destroyed |
| **Blocking** | Blocks when pool exhausted (with timeout) |
| **Types** | Supports connections of different types |

**Classes:** `ConnectionPool`, `PooledConnection`, `PoolStats`

#### 2.3 Token Bucket (`token_bucket.py` — 219 LOC)

**Rate limiting** with configurable burst capacity:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `rate` | 10 | Tokens added per second |
| `burst` | 20 | Maximum token bucket capacity |
| `backoff_factor` | 2.0 | Multiplicative backoff on throttle |
| `max_backoff` | 60s | Maximum backoff delay |

**Returns:** throttle delay in seconds when rate exceeded.

#### 2.4 Adaptive Batcher (`adaptive_batcher.py` — 200 LOC)

**Dynamic batch sizing** based on throughput:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_batch_size` | 1 | Minimum items per batch |
| `max_batch_size` | 100 | Maximum items per batch |
| `batch_window` | 1.0s | Time window for collecting batch |

**Features:** Adaptive sizing based on last batch success/failure, configurable min/max limits.

#### 2.5 Priority Queue (`priority_queue.py` — 173 LOC)

**Priority-ordered task queue:**

| Feature | Description |
|---------|-------------|
| **Priorities** | Higher values = higher priority |
| **Default priority** | Configurable |
| **Max size** | Configurable default |
| **Stats** | Max priority, min priority, size, total enqueued |

**Classes:** `PriorityQueue`, `PriorityItem`, `PriorityQueueStats`

#### 2.6 CAS Store (`cas_store.py` — 126 LOC)

**Compare-and-swap concurrent storage:**

| Feature | Description |
|---------|-------------|
| **`get(key, version)`** | Returns value if version matches |
| **`set(key, value, version)`** | CAS — only writes if version matches |
| **`delete(key, version)`** | CAS delete |
| **`list_keys()`** | All stored keys |

Thread-safe via threading.Lock.

#### 2.7 Queue Pressure (`queue_pressure.py` — 109 LOC)

**Watermark-based pressure monitoring:**

| Level | Condition | Action |
|-------|-----------|--------|
| **LOW** | Below low watermark | Normal operation |
| **MEDIUM** | Between low and high | Throttle non-critical requests |
| **HIGH** | Above high watermark | Backpressure on producers |
| **CRITICAL** | Above critical threshold | Drop lowest priority items |

---

### 3. UltraSales Pipeline (`ultrasales_pipeline.py` — 150 LOC)

**Pre-built end-to-end pipeline** for building the UltraSales marketing OS:

```python
PHASES = {
    "prd_build":     {"points": ["build"],                "agents": 33},
    "development":   {"points": ["architecture", "setup", "code_generation"], "agents": 11},
    "hunting":       {"points": ["bugs", "architecture_review", "security"],  "agents": 11},
    "quality":       {"points": ["audit", "improve", "review"],               "agents": 11},
}
```

Features automated Phase 0→1→2→3→Gate→Loop with kanban status tracking.

---

### 4. YOLO Zones — Escalation-Aware Governance

| Zone | Auto-Approve | Max Parallel | Safety Valve | Use Case |
|------|-------------|--------------|--------------|----------|
| **safe** | No | 5 | Active | Cold start, unknown project |
| **test** | Partial | 11 | Watch | Development-phase test project |
| **staging** | Yes (supervised) | 22 | Triggering | Pre-production build |
| **production** | Yes (full) | 66+ | Blow | Known project, YOLO mode |

**Safety Valve:** Auto-activates after 10 approvals in 5 minutes or 100 LOC changed. Degrades zone one level.

---

### 5. Architecture Docs — 23 Files, 5,115 LOC

Full specification for every component:

| Document | Focus |
|----------|-------|
| `arch/architecture-overview.md` | System architecture |
| `arch/state-machine-architecture.md` | State machine design |
| `arch/mastery-gate-spec.md` | Scoring gate specification |
| `arch/yolo-zones.md` | Zone governance |
| `arch/workspace-manager-spec.md` | Workspace lifecycle |
| `arch/scaling-infrastructure.md` | Scaling design |
| `arch/agent-roles.md` | 198 role definitions |
| `arch/security-audit.md` + `arch/security-audit-l2.md` | Security review |
| `arch/bug-report.md` + 4 variants | Bug tracking |
| `arch/review-report.md` + variants | Code review |
| `arch/audit-report.md` + variants | Code audit |
| `arch/improve-report-l2.md` | Improvement tracking |

---

### 6. Tests — 375+ Tests Across 12 Files

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_scaling.py` | **97** | All 7 scaling modules |
| `test_state_machine.py` | **59** | PhaseMachine, PointMachine, YOLOMachine |
| `test_integration.py` | **48** | Bootstrap → state machine → gate → workspace pipeline |
| `test_workspace_manager.py` | **39** | Scratch/dir/worktree lifecycle |
| `test_gate_11.py` | **29** | Gate11Verifier, handoff validation |
| `test_config.py` | **23** | YAML/JSON config loading |
| `test_mastery_gate.py` | **22** | ScoreCard, verdicts, diversification |
| `test_bootstrap.py` | **21** | Bootstrap flow + YOLO integration |
| `test_synthesizer.py` | **20** | Output merging + dedup |
| `test_agent_roles.py` | **17** | 198 role definitions |

```bash
# Run all tests
python3 -m pytest tests/ -v

# With coverage
python3 -m pytest tests/ --cov=engine --cov=scaling --cov-report=term-missing
```

---

### 7. Project Configuration

**`pyproject.toml`** — Build system, dependencies, CLI entry point:

| Entry | Value |
|-------|-------|
| CLI entry | `hsl = "engine.cli:main"` |
| Python | ≥3.10 |
| Dependencies | pyyaml, rich, click |
| Dev deps | pytest, black, ruff, mypy |

**Config resolution** (3 search paths with JSON fallback):
1. `configs/config.yaml`
2. `config.yaml` (root-level)
3. `config/config.yaml`

**Available configs:**
- `configs/scaling_config.yaml` — Scaling infrastructure defaults
- `configs/yolo_config.yaml` — YOLO zone definitions
- **CI/CD:** `.github/workflows/ci.yml` + `test.yml`

---

### 8. Makefile Targets

```bash
make test       # Run all tests
make lint       # ruff + mypy
make format     # black auto-format
make clean      # Remove __pycache__ + .pyc + .swarm_state.db
```

---

## 🧬 Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                   Hermes Agent (Orchestrator)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Phase 0  │  │ Phase 1  │  │ Phase 2  │  │ Phase 3  │ │
│  │ PRD BUILD│  │ DEVELOP  │  │ HUNTING  │  │ QUALITY  │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       │              │              │              │       │
│  ┌────▼──────────────▼──────────────▼──────────────▼────┐  │
│  │                   Mastery Gate                        │  │
│  │    Correctness  Safety  Coverage  Consistency        │  │
│  │    Diversity  Efficiency  Clarity                     │  │
│  │    Verdict: PASS / CROSS-CHECK / REVIEW / BLOCK      │  │
│  └───────────────────────┬──────────────────────────────┘  │
│                          │ PASS?                            │
│                          ▼ YES                              │
│                     Done ✓                                  │
│                          │ NO → loop Phase 2→3              │
└──────────────────────────────────────────────────────────┘

                    Infrastructure Layer
┌──────────────────────────────────────────────────────────┐
│  Scaling Modules          │  State Machine                │
│  ┌────────────────────┐   │  ┌───────────────────────┐   │
│  │ Circuit Breaker    │   │  │ PhaseMachine          │   │
│  │ Connection Pool    │   │  │ PointMachine          │   │
│  │ Token Bucket       │   │  │ YOLOMachine           │   │
│  │ Adaptive Batcher   │   │  │ StateDB (SQLite WAL)  │   │
│  │ Priority Queue     │   │  └───────────────────────┘   │
│  │ CAS Store          │   │  Workspace Manager           │
│  │ Queue Pressure     │   │  ┌───────────────────────┐   │
│  └────────────────────┘   │  │ Scratch / Dir / Worktr.│   │
│                           │  └───────────────────────┘   │
│  CLI (hsl) ←─► Engine ←─► Scaling ←─► Tests (375+)      │
└──────────────────────────────────────────────────────────┘
```

---

## 💡 Design Philosophy

1. **Sequential phases, parallel points** — phases run one after another; agents within a point run concurrently
2. **Hunt before fix** — Phase 2 (bug hunting) runs BEFORE Phase 3 (quality fixes), not the other way around
3. **YOLO-first** — YOLO mode is default ON for speed; safety valve auto-activates on abuse
4. **Hermes-native** — no subprocess spawning, no Docker-in-Docker; everything via `delegate_task()` and `hermes kanban`
5. **Self-auditing** — every phase updates the skill file with append-only findings; mastery gate enforces quality
6. **Agent diversity** — 33 domains cycled across agents ensure no two agents in a point focus on the same area

---

## 🔗 Related Projects

- **UltraSales** — Built by this framework: `github.com/DominikKrawczyk/ultrasales`  
  Unified Sales & Marketing OS: CMS, Email Inbox, 5 Ad Platforms, Social Suite, Voice AI, Lead Scraper, CRM Kanban, Analytics, Budget Engine, Workflow Automation
