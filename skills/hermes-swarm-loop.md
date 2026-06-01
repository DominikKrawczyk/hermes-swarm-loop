---
name: hermes-swarm-loop
description: Hermes Swarm Loop — 3x3 Ralph Loop with 400-agent swarm. Audit → Improve → Review → Reflect. Bug/security hunting. Self-reflection. Works with DeepSeek, Claude, GPT.
version: 1.0.0
author: Edward Puszczyk
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [swarm, loop, ralph-loop, deepseek, multi-agent, iteration, bounty-hunting, self-reflection]
    related_skills: [claude-code, codex, opencode, hermes-agent]
---

# Hermes Swarm Loop Skill

## When to Use

- Building massive projects (blockchain, infrastructure, full apps)
- Need 400+ agents working in parallel
- Want the 3×3 Ralph Loop (Audit → Improve → Review × 3 × 3)
- Need auto YOLO mode (zero brakes, maximum velocity)
- Want built-in bug hunting + security scanning + architecture review
- Need self-reflection to determine masterpiece vs flawed

## Quick Start

```bash
# Launch full loop
cd /opt/hermes-swarm-loop
./launch.sh --name "MyProject" --desc "Build X" --model deepseek-v4-flash

# Or step by step:
# 1. 400-agent swarm
python launchers/swarm_400.py --name "X" --desc "Build X"

# 2. Ralph Loop iterations
python loop.py --name "X" --desc "Build X" --max-cycles 100

# 3. Bounty hunt
python hunting/bounty_hunter.py --path . --depth 3

# 4. Self-reflection
python reflection/engine.py swarm_state.json
```

## The 3×3 Ralph Loop

```
ITERATION CYCLE N:
  ┌─────────────────────────────────────────────────────┐
  │  [1] AUDIT    → 3 parallel audits → 3 sub-audits   │
  │  [2] IMPROVE  → 3 parallel improves → 3 sub-improves│
  │  [3] REVIEW   → Bug hunt + Arch hunt + Sec hunt     │
  │       └── each with 3 depths × 3 agents             │
  └─────────────────────────────────────────────────────┘
                      ↓
  ┌─────────────────────────────────────────────────────┐
  │  SELF-REFLECTION:                                   │
  │  • Code quality   • Architecture   • Security       │
  │  • Completeness    • Novelty       • Trend          │
  │  → MASTERPIECE? → SHIP IT                           │
  │  → FLAWED?      → LOOP AGAIN (cycle N+1)           │
  └─────────────────────────────────────────────────────┘
```

## 400-Agent Swarm Distribution

| Phase | Agents | Purpose |
|-------|--------|---------|
| Architecture & Planning | 40 | Design the system |
| Code Generation | 200 | Build everything |
| Security Audit | 40 | Find vulnerabilities |
| Bug Hunting | 40 | Find errors |
| Review & Polish | 40 | Quality check |
| Documentation | 40 | Write docs |

## YOLO Mode

When `--yolo` is on:
- No permission prompts
- Auto-approve all file writes
- No brakes, maximum velocity
- Perfect for: "Get shit done" mode

## Self-Reflection Dimensions

1. **Code Quality** — readability, maintainability, test coverage
2. **Architecture** — design decisions, trade-offs, scalability
3. **Security** — vulnerability surface, threat model
4. **Completeness** — does it actually solve the problem?
5. **Novelty** — innovative or rehashing?

Thresholds:
- `score ≥ 0.85 + min ≥ 0.7 + flaws < 5 + cycles ≥ 3 + trend ↑` → **MASTERPIECE**
- Anything less → **LOOP AGAIN**

## Resume from Checkpoint

```bash
# The loop auto-saves state after each batch and cycle
./launch.sh --name "X" --desc "X" --state swarm_state.json

# Or resume specific phase:
python loop.py --name "X" --desc "X" --state swarm_state.json
```

## Push to GitHub

```bash
./launch.sh --name "MyBlockchain" --desc "PoS blockchain" --push
```

Creates repo `hermes-swarm-loop-myblockchain` on your GitHub and pushes everything.
