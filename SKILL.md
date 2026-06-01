---
name: hermes-swarm-loop
description: "3 phases × 3 points × 11 agents. Phase 1: Foundation (PRD build + architecture + setup). Phase 2: Development (AUDIT→IMPROVE→REVIEW). Phase 3: Hunting (BUGS→ARCH→SECURITY). 33 research agents on PRD. First cycle: no iteration logic — just build. Gate at 11 agents per point."
version: 5.0.0
author: Edward Puszczyk
github: DominikKrawczyk
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [ralph-loop, swarm, kanban, prd, research, multi-agent, building]
    related_skills: [claude-code, codex, hermes-agent]
---

# Hermes Swarm Loop — 3×3×11

## What This Is

A **3-phase × 3-point × 11-agent** methodology for building anything from nothing. Uses `hermes kanban swarm` to spawn parallel agents. The first cycle is pure **BUILD** — no iteration logic, no self-reflection. After the first full cycle, iteration gates activate.

**First cycle rule:** No masterpiece/flawed checks. Just build the foundation. Iteration logic starts from cycle 2.

---

## Core Structure

```
PHASE 1: FOUNDATION (3 points × 11 agents = 33 total)
┌─────────────────────────────────────────────────────────────────────┐
│  POINT 1: PRD BUILD                           POINT 2: ARCHITECTURE │
│  ───────────────────────                      ────────────────────  │
│  1. Ask user for PRD (clarify questions)      1. System architecture │
│  2. 33 research agents (domain research)         design based on PRD │
│  3. Format PRD to file with ALL user input     2. Tech stack choice  │
│     as 1:1 quotations (no loss)                3. Component breakdown│
│  4. Generate specification                     │                     │
│                                                 POINT 3: SETUP       │
│  GATE at 11 agents ✅                           ────────────────────  │
│                                                 1. Project scaffolding│
│                                                 2. Dependencies       │
│                                                 3. Configs + CI/CD    │
│                                                 │                     │
│                                                 GATE at 11 agents ✅  │
└─────────────────────────────────────────────────────────────────────┘

PHASE 2: DEVELOPMENT (3 points × 11 agents = 33 total)
┌─────────────────────────────────────────────────────────────────────┐
│  POINT 1: AUDIT                            POINT 2: IMPROVE         │
│  ───────────────────────                   ─────────────────────   │
│  11 agents audit codebase                  11 agents fix issues     │
│  Gate at 11 ✅                              Gate at 11 ✅           │
│                                           POINT 3: REVIEW          │
│                                           ─────────────────────     │
│                                           11 agents verify         │
│                                           Gate at 11 ✅            │
└─────────────────────────────────────────────────────────────────────┘

PHASE 3: HUNTING & QUALITY (3 points × 11 agents = 33 total)
┌─────────────────────────────────────────────────────────────────────┐
│  POINT 1: BUGS                            POINT 2: ARCHITECTURE     │
│  ────────────────                         ───────────────────────  │
│  11 agents bug hunt                       11 agents arch hunt      │
│  Gate at 11 ✅                             Gate at 11 ✅            │
│                                           POINT 3: SECURITY        │
│                                           ─────────────────────     │
│                                           11 agents security hunt  │
│                                           Gate at 11 ✅             │
└─────────────────────────────────────────────────────────────────────┘

     After cycle 1 complete → cycle 2 starts with iteration logic:
     SELF-REFLECTION → MASTERPIECE? → SHIP / LOOP AGAIN / STOP
```

---

## Phase 1: Foundation — BUILD

### Point 1: PRD Build (ASK → 33 RESEARCH → 33 BUILD → FORMAT)

This is the **first action** of the entire framework. **66 agents total** (33 research + 33 build).

**Step 1: Ask user for PRD (via clarify tool)**
Use the `clarify()` tool to ask the user for project requirements. Ask at least these 10 questions:
1. What are you building? (name + one-line description)
2. What is the core problem it solves?
3. Who is the target user?
4. What are the MUST-HAVE features? (list each one)
5. What tech stack preferences? (languages, frameworks, databases)
6. What is NOT in scope? (explicitly excluded features)
7. What is the timeline / deadline?
8. What existing code or resources do you already have?
9. Any constraints or dealbreakers? (budget, performance, compliance)
10. What does success look like? (metrics, milestones)
11. [OPTIONAL] YOLO mode? (ask: "Auto-approve all tool calls?")
12. [OPTIONAL] Cross-model review? (ask: "Use a different model for review?")

**Step 2: 33 research agents (spawn via kanban swarm)**
```bash
hermes kanban swarm \
  --worker default:"Research domain 1/33" \
  ... ×33 \
  --verifier default \
  --synthesizer default \
  "Research project domain — 33 agents"
```

Research topics (distributed across 33 agents):
- Core domain analysis (competitors, landscape, state of the art)
- Technical patterns and best practices for the domain
- Architecture patterns that fit the use case
- Security considerations specific to the domain
- Performance and scalability requirements
- User experience patterns
- Deployment and infrastructure patterns
- Edge cases and failure modes

**Step 3: 33 build agents (spawn via kanban swarm)**
After research completes and verifier passes:

```bash
hermes kanban swarm \
  --worker default:"Build PRD section 1/33" \
  ... ×33 \
  --verifier default \
  --synthesizer default \
  "Build PRD document from research — 33 agents"
```

Build agents:
- Format PRD in custom professional format
- Generate specifications from research findings
- Break down requirements into implementable tasks
- Cross-reference user quotations with research findings
- Generate architecture overview
- Generate success metrics and milestones

**Step 4: Format PRD to file (NO user input loss)**
- ALL user input is preserved as **direct 1:1 quotations** (every word, every message)
- The PRD file uses a Custom Professional Format with long-form descriptions

**Output file:** `PRD_[ProjectName]_v1.0.md` in project root.

```bash
hermes kanban swarm \
  --worker default:"Research domain 1/33" \
  --worker default:"Research domain 2/33" \
  ... ×33 \
  --verifier default \
  --synthesizer default \
  "Research project domain — 33 agents"
```

**Step 3: Format PRD to file (NO user input loss)**
- ALL user input is preserved as direct quotations (1:1)
- The PRD file format is a **Custom Professional Format** with long-form descriptions:

```
# PRD: [Project Name]
# Version: 1.0
# Generated: [date]

## 1. USER QUOTATIONS (preserved 1:1)
> "[Exact user quote 1]"
> "[Exact user quote 2]"
> "...all input preserved without loss..."

## 2. EXECUTIVE SUMMARY
[Long-form synthesis of what this project is]

## 3. PROBLEM STATEMENT
[The core problem being solved]

## 4. TARGET USER & PERSONAS
[Who this is for]

## 5. TECHNICAL REQUIREMENTS
### 5.1 MUST-HAVE Features
- Feature 1: [long description]
- Feature 2: [long description]

### 5.2 NICE-TO-HAVE Features
- ...

### 5.3 Tech Stack (preferred)
- Language:
- Framework:
- Database:
- Infrastructure:

## 6. RESEARCH FINDINGS
[Synthesized from 33 research agents]
- Domain analysis
- Competitor landscape
- Best practices
- Technical recommendations

## 7. SCOPE
### In Scope
### Out of Scope

## 8. ARCHITECTURE OVERVIEW
[High-level system design]

## 9. SUCCESS METRICS

## 10. TIMELINE & MILESTONES
```

**Output file:** `PRD_[ProjectName].md` in project root.

**GATE:** After all 11 agents complete (3 subs), verifier checks PRD completeness. Synthesizer produces final PRD document.

### Point 2: Architecture Design

11 agents design the system architecture based on the PRD:
- 5 agents: System architecture design (components, data flow, interfaces)
- 3 agents: Tech stack finalization (with trade-off analysis)
- 3 agents: Database / storage design

**Output:** `ARCHITECTURE.md` — component diagram, data flow, API contracts, DB schema.

### Point 3: Setup & Scaffolding

11 agents set up the project:
- 4 agents: Project scaffolding (repo structure, build system, package manager)
- 4 agents: Dependencies (all required libraries, tools, frameworks)
- 3 agents: CI/CD pipeline, configs, environment setup

**Output:** Runnable project skeleton with all configs, dependencies, and CI/CD.

---

## Phase 2: Development

### Point 1: AUDIT (11 agents)

11 agents audit the emerging codebase:
- 4 agents: Surface audit — syntax, types, structure, lint
- 4 agents: Deep audit — logic, state management, edge cases
- 3 agents: Exhaustive audit — all files, docs, API contracts

### Point 2: IMPROVE (11 agents)

11 agents implement fixes and features:
- 4 agents: Critical fixes — security, crashes, blocking bugs
- 4 agents: Feature implementation — PRD-mandated features
- 3 agents: Polish — docs, code quality, test coverage

### Point 3: REVIEW (11 agents)

11 agents verify:
- 4 agents: Automated checks — typecheck, lint, test, build
- 4 agents: Manual logic review — read every change
- 3 agents: Quality gate — final sign-off

---

## Phase 3: Hunting & Quality

### Point 1: BUGS (11 agents)
- 4 agents: Syntax & surface bugs
- 4 agents: Deep runtime bugs (race conditions, memory, state)
- 3 agents: Heisenbugs & cascade failures

### Point 2: ARCHITECTURE (11 agents)
- 4 agents: Structure & naming
- 4 agents: Coupling & cohesion
- 3 agents: Scalability & distributed systems

### Point 3: SECURITY (11 agents)
- 4 agents: Surface vulnerabilities
- 4 agents: OWASP top 10
- 3 agents: Advanced (crypto, side channels, supply chain)

---

## First Cycle Rule: BUILD ONLY — NO ITERATION

The first cycle (Phase 1 → 2 → 3) is **BUILD ONLY**:
- No self-reflection jury
- No masterpiece/flawed checks
- No loop-again logic
- Just build the complete foundation through all 3 phases

Iteration logic activates from **cycle 2 onward**:
- After each full cycle, run self-reflection on **6 dimensions**
- **Gate mastery:** Minimum 3 full 3×3 cycles. Findings must be **DIVERSIFIED** across PRD areas (not local to one area). A single-area fix doesn't count as mastery.
- Self-reflection verdicts:
  - **MASTERPIECE** (all 6 ≥ 0.85, flaws < 5, improving ≥ 3 cycles, findings diversified across PRD areas) → SHIP + GITHUB
  - **FLAWED** (any < 0.7 or flaws > 10 or findings not diversified) → LOOP AGAIN
  - **CAN'T IMPROVE** (≥ 3 cycles with < 5% improvement each) → STOP

### Self-Reflection — 6 Dimensions

| # | Dimension | Score 0-1 | What It Measures |
|---|-----------|-----------|------------------|
| 1 | Code Quality | ≥ 0.85 | Readability, maintainability, test coverage, duplication |
| 2 | Architecture | ≥ 0.85 | SOLID, modularity, trade-offs, coupling, scalability |
| 3 | Security | ≥ 0.85 | Vulnerability surface, threat model coverage, defense depth |
| 4 | Completeness | ≥ 0.85 | Full PRD coverage, all features, all edge cases |
| 5 | Novelty | ≥ 0.85 | Innovation vs rehashing, advancement of state |
| 6 | Performance & Scalability | ≥ 0.85 | Speed, resource usage, scaling limits, bottlenecks |

**Diversification rule:** Findings must span at least 3 different PRD areas (e.g., architecture + security + performance, not just 3 architecture fixes). Mastery requires breadth, not just depth.

---

## How to Run a Full Cycle

```bash
# Phase 1: Foundation
hermes kanban boards create my-project
hermes kanban boards switch my-project

# Point 1: PRD Build (ask user, 33 research agents, format PRD)
# Agent asks user for PRD first, then:
hermes kanban swarm --worker ...×33 --verifier default --synthesizer default "Research PRD domain"
hermes kanban dispatch
# → PRD_[ProjectName].md created

# Point 2: Architecture (11 agents)
hermes kanban swarm --worker ...×11 --verifier default --synthesizer default "Design architecture"
hermes kanban dispatch
# → ARCHITECTURE.md created

# Point 3: Setup (11 agents)
hermes kanban swarm --worker ...×11 --verifier default --synthesizer default "Setup project"
hermes kanban dispatch
# → Project skeleton created

# Phase 2: Development
hermes kanban swarm --worker ...×11 --verifier default --synthesizer default "AUDIT"
hermes kanban dispatch
hermes kanban swarm --worker ...×11 --verifier default --synthesizer default "IMPROVE"
hermes kanban dispatch
hermes kanban swarm --worker ...×11 --verifier default --synthesizer default "REVIEW"
hermes kanban dispatch

# Phase 3: Hunting
hermes kanban swarm --worker ...×11 --verifier default --synthesizer default "BUG HUNT"
hermes kanban dispatch
hermes kanban swarm --worker ...×11 --verifier default --synthesizer default "ARCH HUNT"
hermes kanban dispatch
hermes kanban swarm --worker ...×11 --verifier default --synthesizer default "SECURITY HUNT"
hermes kanban dispatch

# Cycle 1 complete. Iteration starts from cycle 2.
# Push to GitHub
git add -A && git commit -m "feat: initial build cycle 1" && git push
```

---

## Comparison

| Feature | Old (v4) | New (v5) — Correct |
|---------|----------|-------------------|
| Structure | 3 loops abstract | 3 phases × 3 points × 11 agents |
| Agents per point | 33 (mixed) | 11 (clear) |
| First cycle | Has iteration logic | BUILD ONLY — no iteration |
| PRD handling | Assumed exists | Active ask + 33 research agents |
| User input preservation | None | 1:1 quotations, no loss |
| PRD format | None | Custom long-form professional format |
| Gate | Per loop | Per point (at 11 agents completed) |
| Research | None | 33 domain research agents |
| Self-reflection | Every 3 cycles | From cycle 2 only |
