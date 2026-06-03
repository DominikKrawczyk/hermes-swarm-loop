# 🐝 Hermes Swarm Loop — 5-Phase Autonomous Build Framework

**Build anything — from zero to production-ready — with structured phases, parallel agent swarms (11→999), and iterative quality loops.**

Inspired by Ralph (19.8k⭐) × Ralphy (2.9k⭐) × ARIS (11.2k⭐) × Hive (10.5k⭐)

## 🔥 Quick Start

```bash
# Clone — works immediately, tests pass out of the box
git clone https://github.com/DominikKrawczyk/hermes-swarm-loop.git
cd hermes-swarm-loop
python3 -m pytest tests/    # 375+ tests ✅

# === PHASE 0: PRD BUILD ===
# 66 build agents: research + web search + precision questions + full PRD
# NO approval prompts — full YOLO mode, zero timeout
python3 bootstrap.py \
  --project-name "EmailPlatform" \
  --project-desc "Multi-tenant email delivery platform with Next.js frontend, FastAPI backend, Docker" \
  --phase prd_build \
  --yolo-zone staging \
  --max-agents 66

# === PHASE 1: DEVELOPMENT ===
# ARCH (11) → SETUP (11) → CODE GENERATION (11) = 33 agents
python3 bootstrap.py \
  --project-name "EmailPlatform" \
  --phase development \
  --yolo-zone test \
  --max-agents 33

# === PHASE 2: HUNTING (find bugs FIRST) ===
# BUGS (11) → ARCH REVIEW (11) → SECURITY (11) = 33 agents
python3 bootstrap.py \
  --project-name "EmailPlatform" \
  --phase hunting \
  --yolo-zone test \
  --max-agents 33

# === PHASE 3: QUALITY (fix based on real bugs) ===
# AUDIT (11) → IMPROVE (11) → REVIEW (11) = 33 agents
python3 bootstrap.py \
  --project-name "EmailPlatform" \
  --phase quality \
  --yolo-zone test \
  --max-agents 33

# === FULL CYCLE (Phase 0→1→2→3) ===
python3 bootstrap.py \
  --project-name "EmailPlatform" \
  --project-desc "..." \
  --yolo-zone staging \
  --max-agents 999
```

## 🧠 Architecture

```
Phase 0: PRD BUILD — 66 agents (all build — research + questions + PRD)
Phase 1: DEVELOPMENT — ARCH (11) → SETUP (11) → CODE (11)
Phase 2: HUNTING — BUGS (11) → ARCH REVIEW (11) → SECURITY (11)   ← RUNS FIRST
Phase 3: QUALITY — AUDIT (11) → IMPROVE (11) → REVIEW (11)        ← THEN FIX

Loop: Phase 2 → Phase 3 → Mastery Gate → PASS? → Done
                                           ↓ NO
                                    Phase 2 → Phase 3 → Gate → ...
```

### Phase 0 — PRD BUILD (66 agents)
66 build agents — każdy robi research + web search + questions + PRD w jednym. Zero timeout, zero approval. Produkuje `PRD.md`.

### Phase 1 — Development (33 agents)
| Point | Agents | Output |
|-------|--------|--------|
| ARCHITECTURE | 11 | System design, component diagrams |
| SETUP | 11 | Project scaffold, configs, CI/CD |
| CODE GENERATION | 11 | Working implementation |

### Phase 2 — Hunting (33 agents) — NOW RUNS FIRST
| Point | Agents | Output |
|-------|--------|--------|
| BUGS | 11 | Bug hunting — real bugs found |
| ARCH REVIEW | 11 | Architecture review, SOLID |
| SECURITY | 11 | Security audit |

### Phase 3 — Quality (33 agents) — NOW RUNS SECOND
| Point | Agents | Output |
|-------|--------|--------|
| AUDIT | 11 | Code audit on ground truth |
| IMPROVE | 11 | Fixes based on real bugs |
| REVIEW | 11 | Quality gate |

## 🔄 Loop Flow

```
Phase 1 (DEVELOPMENT) ── runs ONCE
    ↓
Phase 2 (HUNTING) ── find bugs FIRST
    ↓
Phase 3 (QUALITY) ── then fix
    ↓
Mastery Gate ──→ PASS? → Done
    |               |
    NO ←────────────┘
    (loop Phase 2→Phase 3→Gate)
```

Phase 1 runs EXACTLY ONCE. Phase 2 and Phase 3 alternate (swap pattern) until the Mastery Gate passes.

## 🎯 YOLO Mode

Full auto-approve. No permissions, no brakes, maximum velocity.
Saved permanently in config: `approvals.mode: yolo`, `agent.yolo: true`.

## 📊 Agent Counts

| Phase | Agents | Points |
|-------|--------|--------|
| Phase 0: PRD BUILD | 66 | build |
| Phase 1: Development | 33 | architecture, setup, code_generation |
| Phase 2: Hunting | 33 | bugs, arch_review, security |
| Phase 3: Quality | 33 | audit, improve, review |
| Simplicity | 33 | dead_code, occam, prd_alignment |
| **Total** | **198** | **13 points** |

## 🏗️ Project Structure

```
hermes-swarm-loop/
├── bootstrap.py          # 5-stage launcher (env→DB→phase→YOLO→launch)
├── SKILL.md              # Canonical framework definition
├── engine/               # Core state machines
│   ├── state_machine.py  # SQLite-backed DB, phase/point/YOLO machines
│   ├── mastery_gate.py   # 7-dim scoring & verdict
│   └── ...
├── scaling/              # Scaling layer (token bucket, circuit breaker, etc.)
├── configs/              # YAML configuration
├── tests/                # 375+ tests
│   └── test_agent_roles.py
│   └── test_state_machine.py
│   └── ...
└── arch/                 # Architecture documentation
    ├── agent-roles.md
    ├── architecture-overview.md
    └── ...
```

## 🤖 Clone → Tests → Go

```bash
git clone https://github.com/DominikKrawczyk/hermes-swarm-loop.git
cd hermes-swarm-loop
python3 -m pytest tests/    # 375 passed in 11s ✅
```

Zero setup, zero dependencies beyond Python 3.10+ and `pytest`.

## 📋 Requirements

- Python 3.10+
- `hermes` CLI installed
- `gh` (GitHub CLI) authenticated for GitHub push
- For Phase 0 web search: internet access

## 🔬 Dogfood

The framework improves itself. Run on `/root/code/hermes-swarm-loop/` for self-audit.

---

**🐝 Phase 0 (prd_build) → Phase 1 (development) → Phase 2 (hunting) → Phase 3 (quality). Get shit done. Iterate until masterpiece.**
