# 🐝 Hermes Swarm Loop — Get Shit Done

**The 3×3 Ralph Loop for Hermes + DeepSeek.**

Build anything — blockchain, infrastructure, full applications — with 400-agent swarms, 3-point iteration loops, bug/security hunting, and self-reflection that determines when something is truly a masterpiece.

```
AUDIT → IMPROVE → REVIEW → REFLECT → SHIP or LOOP AGAIN
                ↕ (3× sub-iterations each)
         3 HUNT TYPES: bugs · architecture · security
                ↕ (3 depths × 3 agents each)
         400 AGENTS IN PARALLEL
```

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/DominikKrawczyk/hermes-swarm-loop.git
cd hermes-swarm-loop

# Make launch script executable
chmod +x launch.sh

# Launch full loop
./launch.sh \
  --name "MyBlockchain" \
  --desc "Proof-of-Stake blockchain with smart contracts" \
  --model deepseek-v4-flash \
  --push

# Or step by step:
python launchers/swarm_400.py --name "X" --desc "Build X"
python loop.py --name "X" --desc "Build X" --max-cycles 100
python hunting/bounty_hunter.py --path . --depth 3
python reflection/engine.py swarm_state.json
```

## 🧠 The 3×3 Ralph Loop

```
ITERATION CYCLE N:
  ┌─────────────────────────────────────────────────────┐
  │  [1] AUDIT                                           │
  │    → 10 parallel audit agents                        │
  │    → 3× sub-audits (each spawns 3 more agents)       │
  │    → Total: 19 agents per audit                      │
  │                                                      │
  │  [2] IMPROVE                                          │
  │    → 10 parallel improve agents                      │
  │    → 3× sub-improves (each spawns 3 more agents)     │
  │    → Takes findings from AUDIT and implements fixes   │
  │                                                      │
  │  [3] REVIEW                                           │
  │    → Bug hunters (5 agents)                          │
  │    → Architecture hunters (5 agents)                 │
  │    → Security hunters (5 agents)                     │
  │    → 3× sub-reviews (each spawns 3 more agents)      │
  └─────────────────────────────────────────────────────┘
                      ↓
  ┌─────────────────────────────────────────────────────┐
  │  SELF-REFLECTION                                     │
  │  Evaluates on 5 dimensions:                          │
  │  • Code Quality    • Architecture    • Security      │
  │  • Completeness    • Novelty                        │
  │                                                      │
  │  → MASTERPIECE? → SHIP IT, push to GitHub           │
  │  → FLAWED?      → LOOP AGAIN (with accumulated      │
  │                    context from previous cycles)     │
  └─────────────────────────────────────────────────────┘
```

**Each cycle = 3 points × (1 main + 3 sub) × agents = ~100 agents per iteration.**

## 🔥 400-Agent Swarm

| Phase | Agents | Purpose |
|-------|--------|---------|
| 🏗️ Architecture & Planning | 40 | Design system architecture |
| 💻 Code Generation | 200 | Write all the code |
| 🔒 Security Audit | 40 | Find vulnerabilities |
| 🐛 Bug Hunting | 40 | Find logic errors |
| ✨ Review & Polish | 40 | Quality assurance |
| 📝 Documentation | 40 | Write docs |

## 🎯 YOLO Mode

```bash
--yolo    # Auto-approve everything, zero brakes
```

When you need to **get shit done**:
- No permission prompts
- No confirmation dialogs
- Maximum velocity
- All 400 agents fire at once

## 🔍 Bounty Hunting (3×3×3)

Three hunt types, each with 3 depth levels, each with 3 parallel agents:

```
🐛 BUG HUNTER
  Level 1: Syntax errors, null pointers
  Level 2: Race conditions, memory leaks
  Level 3: Heisenbugs, protocol violations

🏗️ ARCHITECTURE HUNTER
  Level 1: File organization, naming
  Level 2: Coupling, SOLID violations
  Level 3: Scalability, distributed systems

🔒 SECURITY HUNTER
  Level 1: Hardcoded secrets, basic injection
  Level 2: CSRF, XSS, SQL injection, IDOR
  Level 3: Cryptography flaws, side channels
```

## 🪞 Self-Reflection

After each iteration cycle, the framework asks:

> **"Is this a masterpiece or still flawed?"**

| Score | Verdict |
|-------|---------|
| ≥ 0.85 + min ≥ 0.7 + flaws < 5 + cycles ≥ 3 + improving | ✅ **MASTERPIECE** — ship it |
| ≥ 0.7 + improving | 🔄 **Close** — one more cycle |
| < 0.7 or degrading | 🔄 **Continue** — focus on weakest dimension |

## 📦 Project Structure

```
hermes-swarm-loop/
├── loop.py                   # Core loop engine (3×3 Ralph Loop)
├── launch.sh                 # Main launcher script
├── orchestrator/             # Swarm orchestration
│   └── __init__.py
├── agents/                   # Agent templates
│   └── __init__.py
├── skills/
│   └── hermes-swarm-loop.md  # Hermes skill definition
├── hunting/
│   └── bounty_hunter.py      # 3×3×3 hunting engine
├── reflection/
│   └── engine.py             # Self-reflection engine
├── launchers/
│   └── swarm_400.py          # 400-agent swarm launcher
├── examples/                 # Usage examples
├── tests/                    # Test suite
└── README.md                 # This file
```

## 🔄 Resume from Checkpoint

The loop auto-saves state after every batch and cycle:

```bash
# Resume from where you left off
./launch.sh --name "X" --desc "X" --state swarm_state.json

# Resume specific phase
python loop.py --name "X" --desc "X" --state swarm_state.json --max-cycles 50
```

## 🤖 Supported Models

| Model | Flag |
|-------|------|
| DeepSeek V4 Flash | `--model deepseek-v4-flash` |
| Claude Sonnet 4 | `--model claude-sonnet-4` |
| Claude Opus 4 | `--model claude-opus-4` |
| GPT-5 | `--model gpt-5` |
| Any Hermes provider | `--model <provider/model>` |

## 🚀 Push to GitHub

```bash
./launch.sh --name "MyBlockchain" --desc "PoS blockchain" --push
```

Auto-creates `github.com/DominikKrawczyk/hermes-swarm-loop-myblockchain` and pushes all code.

## 📊 Example: Building a Blockchain

```bash
./launch.sh \
  --name "NexusChain" \
  --desc "Layer 1 proof-of-stake blockchain with EVM compatibility, 100k TPS, sharding, and cross-chain bridge" \
  --model deepseek-v4-flash \
  --agents 400 \
  --max-cycles 100 \
  --yolo \
  --push
```

This will:
1. Launch 400 DeepSeek agents to build the entire blockchain
2. Run 3×3 Ralph Loops to iterate until masterpiece
3. Hunt for bugs, architectural flaws, and security vulnerabilities at each iteration
4. Self-reflect to determine when it's truly done
5. Push to GitHub when complete

---

**🐝 Get shit done. Iterate until masterpiece.**
