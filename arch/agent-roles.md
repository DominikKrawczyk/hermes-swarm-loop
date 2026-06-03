# Agent Role Definitions

## Overview

The Hermes Swarm Loop defines 14+ agent roles organized into 5 phases.
Each role has specific skills, outputs, and agent counts. Roles are defined
in `configs/agent_roles.yaml` and dispatched by the kanban swarm system.

```
PHASE STRUCTURE
═══════════════════════════════════════════════════════════════════

Phase 0: PRD BUILD (66 agents, one-time)
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │ 22 research  │  │ 22 questions │  │  22 build    │
  │ agents       │──▶│  agents      │──▶│  agents      │──▶ Full PRD
  └──────────────┘  └──────────────┘  └──────────────┘

Phase 1: DEVELOPMENT (33 agents)
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │ 11 architect │  │  11 setup    │  │ 11 code gen  │
  │ agents       │──▶│  agents      │──▶│  agents      │──▶ Working code
  └──────────────┘  └──────────────┘  └──────────────┘

Phase 2: HUNTING (33 agents)
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │ 11 bugs      │  │ 11 arch rev  │  │ 11 security  │
  │ agents       │──▶│  agents      │──▶│  agents      │──▶ Hardened code
  └──────────────┘  └──────────────┘  └──────────────┘

Phase 3: QUALITY (33 agents)
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │ 11 audit     │  │  11 improve  │  │  11 review   │
  │ agents       │──▶│  agents      │──▶│  agents      │──▶ Verified code
  └──────────────┘  └──────────────┘  └──────────────┘

Phase 4: SIMPLICITY (33 agents)
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │ 11 dead code │  │ 11 occam     │  │ 11 prd align │
  │ agents       │──▶│  agents      │──▶│  agents      │──▶ Refined code
  └──────────────┘  └──────────────┘  └──────────────┘

Total: 198 agents per full cycle (Phase 0 one-time = 66 + 132 per cycle)
```

---

## Phase 0: PRD BUILD — 66 Agents

### Research Agent (22 agents)

**Title:** Research Agent
**Description:** Research domain, competitors, best practices, architecture patterns
**Skills:** web, writing-plans, multi-source-research
**Output:** Research findings organized by domain

Each research agent independently explores the project domain, seeking:
- Existing solutions and architectures
- Best practices and design patterns
- Competitor analysis
- Technology stack recommendations

### Questions Agent (22 agents)

**Title:** Questions Agent
**Description:** Generate precision questions to clarify PRD requirements
**Skills:** web, multi-source-research
**Output:** Clarified PRD requirements

Each questions agent produces refinement questions about:
- Ambiguous or underspecified requirements
- Edge cases and boundary conditions
- Cross-domain dependencies
- Priority and trade-off decisions

### Build Agent (22 agents)

**Title:** PRD Build Agent
**Description:** Format PRD, generate specs, break down requirements
**Skills:** writing-plans, product-requirements-document
**Output:** Professional PRD document

Each build agent synthesizes research findings into:
- Structured product requirements
- Feature breakdowns
- Technical specifications
- User story mapping

---

## Phase 1: DEVELOPMENT — 33 Agents

### Architect Agent (11 agents)

**Title:** Architecture Agent
**Description:** Design system architecture, component diagrams, data flow
**Skills:** architecture-diagram, writing-plans
**Output:** Architecture documentation

Responsibilities:
- Design system architecture and component relationships
- Create data flow diagrams
- Define module boundaries and interfaces
- Evaluate architectural trade-offs
- Document design decisions

### Setup Agent (11 agents)

**Title:** Setup Agent
**Description:** Project setup, directory structure, configs, dependencies
**Skills:** github-repo-management
**Output:** Working project scaffold

Responsibilities:
- Create project directory structure
- Initialize package managers and build systems
- Set up configuration files
- Install dependencies
- Configure CI/CD pipelines

### Code Generation Agent (11 agents)

**Title:** Code Generation Agent
**Description:** Implement core code from architecture specs
**Skills:** test-driven-development
**Output:** Working implementation

Responsibilities:
- Implement core functionality based on architecture
- Write tests alongside implementation (TDD)
- Handle edge cases and error conditions
- Follow project coding standards
- Produce clean, documented code

---

## Phase 2: HUNTING — 33 Agents

### Bug Hunter Agent (11 agents)

**Title:** Bug Hunter
**Description:** Bug hunting — syntax, logic, race conditions, edge cases
**Skills:** systematic-debugging
**Output:** Bug report + fixes

Depth levels:
1. **Shallow:** Syntax errors, type mismatches, obvious null pointers
2. **Medium:** Race conditions, memory leaks, incorrect state management
3. **Deep:** Heisenbugs, concurrency deadlocks, protocol violations

### Architecture Reviewer Agent (11 agents)

**Title:** Architecture Reviewer
**Description:** Architecture review — coupling, SOLID, scalability
**Skills:** architecture-diagram
**Output:** Architecture review report

Checklist:
- Circular dependencies
- God objects / too many responsibilities
- Missing abstraction layers
- Tight coupling between modules
- Violation of single responsibility
- Missing interface segregation
- Scalability bottlenecks
- Single points of failure

### Security Agent (11 agents)

**Title:** Security Agent
**Description:** Security audit — OWASP, secrets, injection, auth
**Skills:** (none specified — security-specific knowledge)
**Output:** Security audit report

Depth levels:
1. **Shallow:** Hardcoded secrets, basic injection, missing auth
2. **Medium:** CSRF, XSS, SQL injection, path traversal, IDOR
3. **Deep:** Cryptography flaws, side channels, supply chain risks

Checklist:
- Hardcoded API keys / secrets
- SQL / NoSQL injection
- Cross-site scripting (XSS)
- Insecure direct object references (IDOR)
- Authentication bypass
- Path traversal
- Cryptographic weaknesses

---

## Phase 3: QUALITY — 33 Agents

### Audit Agent (11 agents)

**Title:** Audit Agent
**Description:** Code audit — syntax, logic, structure, edge cases
**Skills:** codebase-audit, systematic-debugging
**Output:** Audit findings report

Checklist:
- Syntax errors and type mismatches
- Logic errors in conditionals
- Missing error handling
- Dead code and unused imports
- Code style violations
- Edge case gaps

### Improve Agent (11 agents)

**Title:** Improve Agent
**Description:** Fix critical issues, add missing features, polish
**Skills:** systematic-debugging
**Output:** Improved codebase

Responsibilities:
- Address audit findings
- Fix identified bugs
- Add missing error handling
- Improve code structure
- Polish rough edges
- Add documentation where missing

### Review Agent (11 agents)

**Title:** Review Agent
**Description:** Verify fixes, quality gate, regression check
**Skills:** requesting-code-review
**Output:** Quality gate verdict

Checklist:
- Verify all audit issues are addressed
- Check for regression bugs
- Validate test coverage
- Review documentation completeness
- Provide quality gate verdict

---

## Phase 4: SIMPLICITY — 33 Agents

### Dead Code Agent (11 agents)

**Title:** Dead Code Agent
**Description:** Dead code consolidation — find, reposition, not destroy
**Output:** Consolidated codebase

Approach:
- Identify unused functions, classes, imports
- Consolidate rather than delete
- Reposition misplaced code
- Refactor for better organization
- Leverage existing code rather than rewriting

### Occam's Razor Agent (11 agents)

**Title:** Occam's Razor Agent
**Description:** Eliminate bottlenecks, improve efficiency
**Output:** Performance improvements

Approach:
- Identify performance bottlenecks
- Simplify complex logic
- Remove unnecessary abstractions
- Optimize hot paths
- Reduce cognitive complexity
- Apply the simplest correct solution

### PRD Alignment Agent (11 agents)

**Title:** PRD Alignment Agent
**Description:** Compare current state vs PRD vision
**Output:** PRD gap analysis + rebuild triggers

Approach:
- Compare current implementation against PRD
- Identify feature gaps
- Detect scope creep or deviation
- Flag PRD violations requiring rebuild
- Generate gap analysis report

---

## Role Configuration Format

Roles are defined in YAML at `configs/agent_roles.yaml`:

```yaml
phases:
  development:
    points:
      - name: architecture
        agents: 11
        description: "Design system architecture..."
        skills: ["architecture-diagram", "writing-plans"]
        output: "Architecture documentation"
```

## Agent Dispatch

Each agent is dispatched via `hermes chat -q` with:

1. **Skill loading:** Required skills loaded into agent context
2. **Task assignment:** Specific point task with context
3. **Timeout:** Default 120 seconds per agent
4. **Parallel batching:** Agents spawn in parallel batches of 10
5. **Result collection:** Outputs aggregated into point state

## Mastery Gate Per Point

After all 11 agents in a point complete, the Gate11Verifier checks:
- All 11 agents must have completed
- Each handoff must include: summary, worker_id, point, phase
- Handoffs are validated against the schema
- Only when the gate passes does the next point begin
