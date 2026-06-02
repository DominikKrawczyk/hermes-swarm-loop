# 🐝 Hermes Swarm Loop — 3×3×3×N

**Build anything — blockchain, infrastructure, complex applications — with 3-loop autonomous iteration, hive swarm (33→999 agents), cross-model review, and self-reflection that determines when something is truly a masterpiece.**

Inspired by the best of: [Ralph Loop](https://github.com/snarktank/ralph) (19.8k⭐) × [Ralphy](https://github.com/michaelshimeles/ralphy) (2.9k⭐) × [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) (11.2k⭐) × [Hive](https://github.com/aden-hive/hive) (10.5k⭐)

```
┌──────────────────────────────────────────────────────────────────────┐
│             LOOP 1: DEVELOPMENT (AUDIT → IMPROVE → REVIEW)           │
│                   × 3 sub-iterations each × N agents                 │
├──────────────────────────────────────────────────────────────────────┤
│             LOOP 2: HUNTING (BUGS → ARCHITECTURE → SECURITY)         │
│                   × 3 depths each × N agents                         │
├──────────────────────────────────────────────────────────────────────┤
│             LOOP 3: SIMPLICITY & CONSOLIDATION                       │
│             1. Dead Code Audit + Consolidate (NOT destroy)           │
│             2. Occam's Razor (bottlenecks reduction)                 │
│             3. PRD Alignment ← BACK TO LOOP 1                        │
├──────────────────────────────────────────────────────────────────────┤
│             SELF-REFLECTION JURY × cross-model review                │
│             → MASTERPIECE / FLAWED (loop again) / CAN'T IMPROVE      │
│             SWARM: 33→999 agents | YOLO mode                         │
└──────────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

This is a **prompt/skill methodology** for [Hermes Agent](https://github.com/DominikKrawczyk/hermes-agent). No Python code to run—just load the skill.

```bash
# Clone
git clone https://github.com/DominikKrawczyk/hermes-swarm-loop.git
cd hermes-swarm-loop

# Use as a skill in Hermes:
# "Load the hermes-swarm-loop skill and run a 3-loop cycle on /path/to/project — N=33, yolo"

# Eat your own dogfood:
# "Load the hermes-swarm-loop skill and run a 3-loop cycle on /opt/hermes-swarm-loop/ — N=33"
```

## 🧠 The 3×3×3×N Architecture

### Loop 1 — Development (AUDIT → IMPROVE → REVIEW)

| Point | Sub 1 | Sub 2 | Sub 3 |
|-------|-------|-------|-------|
| **AUDIT** | Surface: syntax, types, structure | Deep: logic, state, error handling | Exhaustive: all files, edge cases, docs |
| **IMPROVE** | Critical: security, crashes | Feature: missing functionality | Polish: perf, docs, quality |
| **REVIEW** | Auto-verify: lint, test, build | Manual logic review | Final quality gate |

### Loop 2 — Hunting (BUGS → ARCHITECTURE → SECURITY)

| Hunt | L1: Surface | L2: Deep | L3: Expert |
|------|-------------|----------|------------|
| **🐛 BUGS** | Syntax, null pointers, off-by-one | Race conditions, memory leaks | Heisenbugs, protocol violations |
| **🏗️ ARCH** | Structure, naming, patterns | Coupling, SOLID, DI, tech debt | Scalability, CAP, distributed |
| **🔒 SECURITY** | Secrets, injection, auth | OWASP Top 10 (XSS, CSRF, IDOR) | Crypto, side channels, supply chain |

### Loop 3 — Simplicity & Consolidation

1. **Dead Code Audit + Consolidation** — find dead/redundant code, REPOSITION rather than delete, consolidate into shared utilities, slight architectural refactoring (no rewrites)
2. **Operational Occam's Razor** — eliminate testing bottlenecks, CI/CD inefficiencies, build/deploy slowdowns, tooling overhead
3. **PRD Alignment Audit** — compare HAP (current state) vs PRD vision, account for Loop 1 & 2 changes, feed PRD gap errors back to Loop 1. **ALIGNMENT, not further looping.**

### Self-Reflection Jury

After all 3 loops complete, a cross-model jury evaluates on 5 dimensions:

| Dimension | Score (0-1) | Evidence |
|-----------|-------------|----------|
| Code Quality | ≥ 0.85 | Readability, maintainability, test coverage |
| Architecture | ≥ 0.85 | Design quality, SOLID, scalability |
| Security | ≥ 0.85 | Vulnerability surface, threat model |
| Completeness | ≥ 0.85 | Full PRD coverage, all features |
| Novelty | ≥ 0.85 | Innovative approach vs rehashing |

**Outcomes:**
- ✅ **MASTERPIECE** (all ≥ 0.85, flaws < 5, improving ≥ 3 cycles) → SHIP + GITHUB
- 🔄 **FLAWED** (any < 0.7 or flaws > 10) → LOOP AGAIN on weakest dimension
- ⏹️ **CAN'T IMPROVE** (3+ cycles flat) → STOP + analysis report

## 🔥 Hive Swarm (33→999 Agents)

Start small (33), scale up based on findings volume:

| Scale | Agents | When |
|-------|--------|------|
| Small | 33 | First cycle, small project |
| Medium | 100 | After first 2 cycles |
| Large | 400 | Complex projects |
| Maximum | 999 | Full-stack blockchain, massive infrastructure |

## 🎯 YOLO Mode

Auto-approve ALL tool calls. No permissions, no brakes, maximum velocity.
Activate with: `YOLO=true` or pass `--yolo` in task description.

## 🔄 Cross-Model Review (Inspired by ARIS)

**Core principle: "A loop can DRIVE, it cannot ACQUIT"**

- **Executor** (DeepSeek): checks execution completeness — "was the task finished?"
- **Reviewer** (different model family — Claude/GPT/Gemini): checks quality and correctness
- Breaks self-play blind spots: the same model reviewing its own work misses patterns

## 📦 Project Structure

```
hermes-swarm-loop/
├── SKILL.md                        # v4.0.0 — the actual framework (this is THE framework)
├── README.md                       # This file
├── launch.sh                       # Legacy launcher (shell-based)
├── archive/
│   └── python-v2.0.0/              # Archived old Python-based version
└── swarm_33_audit.sh               # Script: 33-agent AUDIT swarm example
```

## 🔬 Eat Your Own Dogfood

The framework improves itself. Run the 3-loop cycle on `/opt/hermes-swarm-loop/`:

1. **Loop 1:** AUDIT the framework files → IMPROVE → REVIEW
2. **Loop 2:** Hunt for bugs, architecture flaws, security issues in the framework
3. **Loop 3:** Consolidate dead code, reduce operational complexity, align with PRD
4. **Self-reflect:** Is the framework itself a masterpiece?
5. **Push** improved framework to GitHub
6. **Repeat**

## 📊 Comparison: vs Original Ralph

| Feature | Ralph (snarktank) | Hermes Swarm Loop |
|---------|-------------------|-------------------|
| Loop structure | 1 task → implement → check → repeat | 3 loops × 3 points × 3 sub × N |
| Points per iteration | 1 story | 9 (3 dev + 3 hunt + 3 simplicity) |
| Multiplier | 1× | 3×3×3×N |
| Parallel agents | 1 | Up to 999 |
| Hunting | None | Bugs + Architecture + Security ×3 depths |
| Simplicity audit | None | Dead code consolidation + Occam's Razor + PRD Alignment |
| Review model | Self-review | Cross-model review (executor ≠ reviewer) |
| Self-reflection | Pass/fail | 5-dimension masterpiece/flawed/cannot-improve |
| YOLO | No | Yes |
| Model agnostic | Claude/Amp | DeepSeek, Claude, GPT, Gemini, any |

## 🤖 Supported Models

Hermes supports any LLM provider. The framework works with:
- DeepSeek V4 Flash / Pro
- Claude (Sonnet 4, Opus 4)
- GPT-5 / GPT-5.5
- Gemini 3
- Any other via Hermes provider config

---

**🐝 Get shit done. Iterate until masterpiece.**
