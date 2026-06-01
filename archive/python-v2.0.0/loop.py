#!/usr/bin/env python3
"""
Hermes Swarm Loop — Get Shit Done
The REAL 3×3 Ralph Loop for Hermes + DeepSeek.

REAL agents. REAL code changes. REAL audits. REAL bug hunting.

Architecture:
  3-point loop: AUDIT → IMPROVE → REVIEW (each × 3 sub × 3 agents)
  3 hunt types: bugs, architecture, security (each × 3 depths × 3 agents)
  400 agents via hermes chat -q
  Self-reflection: masterpiece or flawed?
  Auto YOLO mode: zero brakes

USAGE:
  # Run on a project (eats own dogfood too):
  python loop.py --dir /path/to/project --name "Project" --desc "Description"
  
  # Resume:
  python loop.py --state swarm_state.json
"""

import os, sys, json, time, glob, re, subprocess, threading
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

VERSION = "2.0.0"
HERMES_CMD = "hermes"


# ─── AGENT SPAWNER — REAL Hermes agents ─────────────────────────

def spawn_agent(task: str, context: str = "", model: str = "deepseek-v4-flash",
                workdir: str = ".", timeout: int = 120) -> dict:
    """
    Spawn a REAL Hermes agent via `hermes chat -q`.
    
    The agent reads files, analyzes, writes code, audits — whatever the task says.
    Returns dict with stdout, exit_code, duration.
    """
    prompt = f"""{context}

TASK: {task}

You are a Hermes Swarm Loop agent. Do your task thoroughly.
- Read all relevant files first
- Analyze everything
- Make changes if needed
- Report what you found and what you did
- BE SPECIFIC with file paths, line numbers, and exact issues
"""
    # Escape for shell
    prompt_escaped = prompt.replace('"', '\\"').replace('`', '\\`').replace('$', '\\$')
    
    cmd = (
        f'{HERMES_CMD} chat -q "{prompt_escaped}" '
        f'--model {model} '
        f'--max-turns 15 '
        f'--quiet'
    )
    
    start = time.time()
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=workdir
        )
        duration = time.time() - start
        output = (result.stdout or "") + (result.stderr or "")
        return {
            "success": result.returncode == 0,
            "output": output[:5000],
            "duration": round(duration, 1),
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "TIMEOUT", "duration": timeout, "exit_code": -1}
    except Exception as e:
        return {"success": False, "output": str(e), "duration": 0, "exit_code": -1}


def spawn_agents_parallel(tasks: list[dict], max_workers: int = 10,
                           model: str = "deepseek-v4-flash",
                           workdir: str = ".") -> list[dict]:
    """Spawn multiple Hermes agents in parallel."""
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for i, t in enumerate(tasks):
            f = executor.submit(
                spawn_agent, t["task"], t.get("context", ""),
                model, workdir, t.get("timeout", 120)
            )
            futures[f] = i
        
        for f in as_completed(futures):
            idx = futures[f]
            try:
                r = f.result()
                r["task_idx"] = idx
                r["task_name"] = tasks[idx].get("name", f"task_{idx}")
                results.append(r)
            except Exception as e:
                results.append({
                    "success": False, "output": str(e),
                    "task_idx": idx, "task_name": tasks[idx].get("name", f"task_{idx}"),
                    "duration": 0, "exit_code": -1
                })
    
    results.sort(key=lambda x: x.get("task_idx", 0))
    return results


# ─── FILE ANALYSIS ───────────────────────────────────────────────

def get_project_files(path: str, extensions: list[str] = None) -> list[str]:
    """Get all source files in a project."""
    if extensions is None:
        extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.rs', '.go', '.java',
                      '.c', '.cpp', '.h', '.hpp', '.sol', '.json', '.yaml', '.toml',
                      '.md', '.sh', '.bash', '.css', '.html']
    files = []
    for ext in extensions:
        found = glob.glob(f"{path}/**/*{ext}", recursive=True)
        # Skip hidden dirs and node_modules, venv, .git
        files.extend([
            f for f in found
            if not any(p in f for p in ['/node_modules/', '/venv/', '/.git/', 
                                         '/__pycache__/', '/.hermes/', '/build/',
                                         '/target/', '/dist/', '.min.'])
        ])
    return sorted(files)


def analyze_project_structure(path: str) -> dict:
    """Quick project structure analysis."""
    files = get_project_files(path)
    stats = {}
    for f in files:
        ext = Path(f).suffix
        stats[ext] = stats.get(ext, 0) + 1
    
    try:
        total_lines = sum(1 for f in files for _ in open(f, errors='ignore'))
    except:
        total_lines = 0
    
    return {
        "total_files": len(files),
        "total_lines": total_lines,
        "by_extension": stats,
        "file_list": files[:50],  # First 50
    }


# ─── DATA MODELS ─────────────────────────────────────────────────

@dataclass
class IterationState:
    cycle: int
    audit: dict = field(default_factory=lambda: {"findings": [], "agents": [], "subs": []})
    improve: dict = field(default_factory=lambda: {"changes": [], "agents": [], "subs": []})
    review: dict = field(default_factory=lambda: {"feedback": [], "agents": [], "subs": []})
    reflection: Optional[dict] = None
    is_masterpiece: bool = False
    flaws_found: int = 99
    agents_used: int = 0
    started_at: float = 0.0
    completed_at: float = 0.0

@dataclass
class Session:
    name: str
    description: str
    workdir: str
    goal: str = ""
    total_agents: int = 0
    total_cycles: int = 0
    started_at: float = 0.0
    completed_at: float = 0.0
    history: list = field(default_factory=list)


# ─── CORE LOOP ───────────────────────────────────────────────────

class RalphLoop:
    """The 3×3 Ralph Loop. Real agents. Real work. Real results."""
    
    def __init__(self, session: Session, model: str = "deepseek-v4-flash",
                 max_agents: int = 400, yolo: bool = True):
        self.session = session
        self.model = model
        self.max_agents = max_agents
        self.yolo = yolo
        self._stop = False
        self.session.started_at = time.time()
    
    def stop(self):
        self._stop = True
    
    def phase_swarm_400(self):
        """Phase 1: Launch 400 agents across 6 workstreams."""
        path = self.session.workdir
        proj_name = self.session.name
        
        print(f"\n{'#'*60}")
        print(f"🐝 PHASE 1: 400-AGENT SWARM")
        print(f"{'#'*60}")
        print(f"  Target: {path}")
        print(f"  Model:  {self.model}")
        print(f"{'#'*60}\n")
        
        phases = [
            ("🏗️ Architecture & Planning", 40, [
                {"name": f"arch_{i}", "task": f"Analyze the architecture of {proj_name} at {path}. Read all key files. Identify: design patterns used, architecture flaws, coupling issues, missing abstractions. Output specific findings with file paths.",
                 "context": f"Project: {proj_name}\nDescription: {self.session.description}\nGoal: {self.session.goal}"}
                for i in range(40)
            ]),
            ("💻 Code Generation", 200, [
                {"name": f"code_{i}", "task": f"Write and improve code for {proj_name}. Read existing files, find what needs to be built or improved, implement it. Focus on: new features, missing functionality, code quality improvements.",
                 "context": f"Project: {proj_name}\nWorkdir: {path}"}
                for i in range(200)
            ]),
            ("🔒 Security Audit", 40, [
                {"name": f"sec_{i}", "task": f"Security audit of {proj_name}. Read all source files. Find: injection vulns, auth flaws, crypto weaknesses, hardcoded secrets, path traversal, IDOR. CRITICAL: report exact file paths and lines.",
                 "context": f"Project: {proj_name}"}
                for i in range(40)
            ]),
            ("🐛 Bug Hunting", 40, [
                {"name": f"bug_{i}", "task": f"BUG HUNT: read all source files in {proj_name}. Find: null pointers, race conditions, memory leaks, logic errors, edge cases, type errors, off-by-one. Report exact file:line for each bug.",
                 "context": f"Project: {proj_name}"}
                for i in range(40)
            ]),
            ("✨ Review & Polish", 40, [
                {"name": f"review_{i}", "task": f"Code review of {proj_name}. Read all files. Check: code style, documentation, test coverage, error handling, edge cases, performance. Suggest specific improvements with file paths.",
                 "context": f"Project: {proj_name}"}
                for i in range(40)
            ]),
            ("📝 Documentation", 40, [
                {"name": f"docs_{i}", "task": f"Write/improve documentation for {proj_name}. Read the code, understand the architecture, then write: API docs, setup guide, architecture overview, examples.",
                 "context": f"Project: {proj_name}\nWorkdir: {path}"}
                for i in range(40)
            ]),
        ]
        
        total_agents = 0
        for phase_name, count, tasks in phases:
            if self._stop:
                break
            print(f"\n{phase_name} — {count} agents")
            
            # Launch in batches of 10 (parallel)
            batch_size = min(10, count)
            for batch_start in range(0, count, batch_size):
                if self._stop:
                    break
                batch = tasks[batch_start:batch_start + batch_size]
                print(f"  Batch {batch_start//batch_size + 1}/{(count+batch_size-1)//batch_size}...")
                
                results = spawn_agents_parallel(
                    batch, max_workers=batch_size,
                    model=self.model, workdir=path
                )
                
                successes = sum(1 for r in results if r.get("success"))
                total_agents += len(results)
                self.session.total_agents += len(results)
                print(f"    ✅ {successes}/{len(results)} agents completed")
        
        print(f"\n✅ Phase 1 complete: {total_agents} agents deployed")
        return total_agents
    
    def run_iteration(self) -> IterationState:
        """One full 3×3 Ralph Loop iteration with REAL agents."""
        self.session.total_cycles += 1
        cycle = self.session.total_cycles
        state = IterationState(cycle=cycle, started_at=time.time())
        path = self.session.workdir
        
        print(f"\n{'='*60}")
        print(f"🌀 RALPH LOOP — CYCLE {cycle}")
        print(f"{'='*60}")
        print(f"  Project: {self.session.name}")
        print(f"  Agents used so far: {self.session.total_agents}")
        print(f"{'='*60}\n")
        
        # ─── POINT 1: AUDIT (3 agents × 3 sub-audits) ───
        print(f"\n🔍 [1/3] AUDIT — Real code analysis")
        
        project_info = analyze_project_structure(path)
        print(f"  Found {project_info['total_files']} files ({project_info['total_lines']} lines)")
        
        # Main audit agents (3 parallel)
        audit_tasks = [
            {"name": "audit_main_1", "task": f"Deep code audit of {self.session.name} at {path}. Read ALL files. Find: code quality issues, dead code, duplication, missing error handling, anti-patterns. Report exact file:line.",
             "context": f"Files: {json.dumps(project_info['file_list'][:20])}"},
            {"name": "audit_main_2", "task": f"Architecture audit of {self.session.name}. Read all files. Find: design flaws, coupling issues, scalability constraints, SOLID violations, missing abstractions.",
             "context": f"Project: {self.session.name}"},
            {"name": "audit_main_3", "task": f"Performance & security audit of {self.session.name}. Read all files. Find: bottlenecks, N+1 queries, memory issues, injection vulns, auth flaws.",
             "context": f"Project: {self.session.name}"},
        ]
        print(f"  → Spawning {len(audit_tasks)} audit agents...")
        audit_results = spawn_agents_parallel(audit_tasks, model=self.model, workdir=path)
        state.audit["agents"] = audit_results
        state.agents_used += len(audit_results)
        
        # Sub-audits (3 × 3 agents)
        for sub_i in range(3):
            if self._stop: break
            print(f"  └─ Sub-audit {sub_i+1}/3 — {3} agents")
            sub_tasks = [
                {"name": f"audit_sub_{sub_i}_a1", "task": f"Sub-audit #{sub_i+1}: deeper analysis of {self.session.name}. Read files you haven't read yet. Find issues the main audit missed.",
                 "context": f"Previous findings: {[a.get('output','')[:200] for a in audit_results]}"}
                for _ in range(3)
            ]
            sub_results = spawn_agents_parallel(sub_tasks, model=self.model, workdir=path)
            state.audit["subs"].append(sub_results)
            state.agents_used += len(sub_results)
        
        if self._stop: return state
        
        # ─── POINT 2: IMPROVE (3 agents × 3 sub-improves) ───
        print(f"\n🔧 [2/3] IMPROVE — Real code changes")
        improve_tasks = [
            {"name": "improve_main_1", "task": f"Implement the most critical improvements in {self.session.name}. Read files, make REAL code changes: fix bugs, improve error handling, add missing features. WRITE THE CODE.",
             "context": f"Project: {self.session.name}\nWorkdir: {path}"},
            {"name": "improve_main_2", "task": f"Refactor code in {self.session.name}. Read files, restructure where needed: extract functions, add types, improve modularity. MAKE REAL CHANGES.",
             "context": f"Project: {self.session.name}"},
            {"name": "improve_main_3", "task": f"Add tests and documentation to {self.session.name}. Read code, write tests, add docstrings, improve README. MAKE REAL FILES.",
             "context": f"Project: {self.session.name}\nWorkdir: {path}"},
        ]
        print(f"  → Spawning {len(improve_tasks)} improve agents...")
        improve_results = spawn_agents_parallel(improve_tasks, model=self.model, workdir=path)
        state.improve["agents"] = improve_results
        state.agents_used += len(improve_results)
        
        for sub_i in range(3):
            if self._stop: break
            print(f"  └─ Sub-improve {sub_i+1}/3 — {3} agents")
            sub_tasks = [
                {"name": f"improve_sub_{sub_i}_a1", "task": f"Sub-improvement #{sub_i+1}: refine and polish {self.session.name}. Fix remaining issues, improve code quality, add edge case handling.",
                 "context": f"Previous changes: {[a.get('output','')[:200] for a in improve_results]}"}
                for _ in range(3)
            ]
            sub_results = spawn_agents_parallel(sub_tasks, model=self.model, workdir=path)
            state.improve["subs"].append(sub_results)
            state.agents_used += len(sub_results)
        
        if self._stop: return state
        
        # ─── POINT 3: REVIEW with 3 hunt types × 3 depths × 3 agents ───
        print(f"\n📋 [3/3] REVIEW — Bug, Arch & Security hunting")
        
        for hunt_type, agents_count in [("bugs", 5), ("architecture", 5), ("security", 5)]:
            if self._stop: break
            print(f"  └─ Hunting: {hunt_type.upper()} ({agents_count} agents)")
            hunt_tasks = [
                {"name": f"hunt_{hunt_type}_{i}", "task": f"{hunt_type.upper()} HUNT #{i+1} for {self.session.name}. Read ALL files. Find EVERY {hunt_type} issue. Report exact file:line. BE THOROUGH.",
                 "context": f"Project: {self.session.name}\nType: {hunt_type}"}
                for i in range(agents_count)
            ]
            hunt_results = spawn_agents_parallel(hunt_tasks, model=self.model, workdir=path)
            state.review["feedback"].extend(hunt_results)
            state.review["agents"].extend(hunt_results)
            state.agents_used += len(hunt_results)
        
        for sub_i in range(3):
            if self._stop: break
            print(f"  └─ Sub-review {sub_i+1}/3 — 3 agents")
            sub_tasks = [
                {"name": f"review_sub_{sub_i}_a{i}", "task": f"Final review #{sub_i+1}.{i+1}: read all files in {self.session.name} one more time. Find ANY remaining issue. Be the final quality gate.",
                 "context": f"Cycle: {cycle}"}
                for i in range(3)
            ]
            sub_results = spawn_agents_parallel(sub_tasks, model=self.model, workdir=path)
            state.review["subs"].append(sub_results)
            state.agents_used += len(sub_results)
        
        if self._stop: return state
        
        # ─── SELF-REFLECTION ───
        print(f"\n🪞 SELF-REFLECTION — Real analysis")
        
        # Count findings from all outputs
        all_outputs = []
        for agent_list in [state.audit["agents"]] + state.audit["subs"] + \
                          [state.improve["agents"]] + state.improve["subs"] + \
                          [state.review["agents"]] + state.review["subs"]:
            for a in (agent_list if isinstance(agent_list, list) else []):
                out = a.get("output", "")
                if out:
                    all_outputs.append(out)
        
        total_findings = sum(1 for o in all_outputs if any(kw in o.lower() 
            for kw in ["bug", "issue", "error", "vuln", "flaw", "problem", "fix", "warning"]))
        
        flaws_found = max(0, total_findings - len(all_outputs))  # rough heuristic
        
        # Real self-reflection via an agent
        reflection_prompt = (
            f"You are the self-reflection engine for Hermes Swarm Loop.\n"
            f"Project: {self.session.name}\n"
            f"Cycle: {cycle}\n"
            f"Total agents used this cycle: {state.agents_used}\n\n"
            f"Analyze these agent outputs and determine:\n"
            f"1. Is this project a MASTERPIECE (ready to ship) or still FLAWED?\n"
            f"2. How many flaws remain? (0-100)\n"
            f"3. What is the weakest area?\n"
            f"4. Can it be further improved?\n\n"
            f"Agent outputs (sample):\n" + "\n---\n".join(o[:500] for o in all_outputs[:10]) +
            f"\n\nRespond in JSON format: {{\"is_masterpiece\": bool, \"flaws_remaining\": int, "
            f"\"weakest_area\": str, \"confidence\": float, \"can_improve\": bool}}"
        )
        
        reflection_agent = spawn_agent(
            reflection_prompt, model=self.model, workdir=path, timeout=60
        )
        
        # Parse reflection result
        try:
            import re as _re
            json_match = _re.search(r'\{.*\}', reflection_agent.get("output", "{}"), _re.DOTALL)
            if json_match:
                state.reflection = json.loads(json_match.group())
            else:
                state.reflection = {"is_masterpiece": False, "flaws_remaining": flaws_found, "confidence": 0.3}
        except:
            state.reflection = {"is_masterpiece": False, "flaws_remaining": flaws_found, "confidence": 0.3}
        
        state.is_masterpiece = state.reflection.get("is_masterpiece", False)
        state.flaws_found = state.reflection.get("flaws_remaining", flaws_found)
        state.completed_at = time.time()
        
        # ─── REPORT ───
        self._print_cycle_report(state)
        
        self.session.history.append(asdict(state) if hasattr(state, '__dict__') else state)
        self._save_state()
        
        return state
    
    def run_until_masterpiece(self, max_cycles: int = 100):
        """Keep looping until masterpiece."""
        print(f"\n{'#'*60}")
        print(f"🏁 HERMES SWARM LOOP — Starting")
        print(f"  Project: {self.session.name}")
        print(f"  Max cycles: {max_cycles}")
        print(f"  Model: {self.model}")
        print(f"  YOLO: {'⚠️ ON' if self.yolo else 'normal'}")
        print(f"  Workdir: {self.session.workdir}")
        print(f"{'#'*60}\n")
        
        while self.session.total_cycles < max_cycles and not self._stop:
            state = self.run_iteration()
            
            if state.is_masterpiece:
                print(f"\n{'★'*60}")
                print(f"🌟 MASTERPIECE — Cycle {state.cycle}")
                print(f"{'★'*60}")
                self.session.completed_at = time.time()
                self._print_final_report()
                self._save_state()
                return state
            
            if self.session.total_cycles >= max_cycles:
                print(f"\n⚠️ Max cycles ({max_cycles}) reached.")
                break
        
        self.session.completed_at = time.time()
        self._save_state()
        return None
    
    def _print_cycle_report(self, state: IterationState):
        """Print human-readable cycle report."""
        duration = state.completed_at - state.started_at if state.completed_at else 0
        print(f"\n{'─'*50}")
        print(f"  CYCLE {state.cycle} COMPLETE")
        print(f"  Duration: {duration:.0f}s")
        print(f"  Agents used: {state.agents_used}")
        print(f"  Flaws remaining: {state.flaws_found}")
        print(f"  Masterpiece: {'✅' if state.is_masterpiece else '🔄 NO'}")
        if state.reflection:
            print(f"  Confidence: {state.reflection.get('confidence', 0):.0%}")
            print(f"  Weakest: {state.reflection.get('weakest_area', 'unknown')}")
        print(f"{'─'*50}\n")
    
    def _print_final_report(self):
        """Final report."""
        dur = (self.session.completed_at or time.time()) - self.session.started_at
        print(f"\n{'='*60}")
        print(f"📊 FINAL REPORT")
        print(f"{'='*60}")
        print(f"  Project: {self.session.name}")
        print(f"  Cycles: {self.session.total_cycles}")
        print(f"  Total agents: {self.session.total_agents}")
        print(f"  Duration: {dur:.0f}s ({dur/60:.1f}min)")
        print(f"{'='*60}")
    
    def _save_state(self, path: str = "swarm_state.json"):
        """Save session state."""
        data = {
            "session": asdict(self.session) if hasattr(self.session, '__dict__') else str(self.session),
            "version": VERSION,
            "saved_at": datetime.now().isoformat(),
        }
        with open(os.path.join(self.session.workdir, path), "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"💾 State saved to {path}")


# ─── ENTRY POINT ─────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description=f"Hermes Swarm Loop v{VERSION}")
    parser.add_argument("--dir", "-d", default=".", help="Project directory")
    parser.add_argument("--name", "-n", required=True, help="Project name")
    parser.add_argument("--desc", help="Project description")
    parser.add_argument("--goal", help="Project goal")
    parser.add_argument("--model", "-m", default="deepseek-v4-flash", help="Agent model")
    parser.add_argument("--max-cycles", type=int, default=10, help="Max iterations")
    parser.add_argument("--max-agents", type=int, default=400, help="Max agents")
    parser.add_argument("--yolo", action="store_true", default=True, help="YOLO mode")
    parser.add_argument("--state", help="Resume from state file")
    parser.add_argument("--swarm-only", action="store_true", help="Only run 400-agent swarm (no loop)")
    parser.add_argument("--loop-only", action="store_true", help="Only run Ralph Loop (no swarm)")
    
    args = parser.parse_args()
    
    if args.state:
        with open(args.state) as f:
            data = json.load(f)
        session = Session(**data.get("session", {}))
    else:
        session = Session(
            name=args.name,
            description=args.desc or args.name,
            workdir=os.path.abspath(args.dir),
            goal=args.goal or args.desc or args.name,
        )
    
    loop = RalphLoop(session, model=args.model, max_agents=args.max_agents, yolo=args.yolo)
    
    try:
        if not args.loop_only:
            loop.phase_swarm_400()
        
        if not args.swarm_only:
            loop.run_until_masterpiece(max_cycles=args.max_cycles)
        
        loop._save_state()
        print(f"\n✅ Done. Final state saved.")
        
    except KeyboardInterrupt:
        print(f"\n⛔ Interrupted at cycle {session.total_cycles}")
        loop._save_state()
        print("💾 Resume with: python loop.py --state swarm_state.json")


if __name__ == "__main__":
    main()
