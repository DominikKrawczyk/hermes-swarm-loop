# Hermes Swarm Loop — 400-Agent Launcher
# Usage: python launchers/swarm_400.py "Build a blockchain" --model deepseek-v4-flash

"""
400-Agent Swarm Launcher for DeepSeek/Claude/Hermes.

Launches N agents in parallel batches, each working on a slice of the project.
Automatically distributes work across:
- Code generation agents
- Architecture agents
- Security agents
- Test agents
- Documentation agents

Each batch spawns up to parallel_batches agents, waits for completion,
then spawns the next batch. Results are aggregated into the project context.
"""

import sys
import os
import json
import time
import subprocess
import threading
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from loop import RalphLoop, ProjectContext, SwarmConfig, IterationState, save_state


class Swarm400:
    """Launch and manage 400 parallel agents."""
    
    def __init__(self, 
                 project: ProjectContext,
                 config: Optional[SwarmConfig] = None,
                 loop: Optional[RalphLoop] = None):
        self.project = project
        self.config = config or SwarmConfig(max_agents=400)
        self.loop = loop or RalphLoop(project=project, swarm_config=self.config)
        self.active_agents: list[dict] = []
        self.completed_agents: list[dict] = []
        self._lock = threading.Lock()
    
    def launch_wave(self, count: int, task_type: str, context: dict) -> list[dict]:
        """Launch a wave of parallel agents."""
        actual = min(count, self.config.max_agents - len(self.completed_agents))
        if actual <= 0:
            return []
        
        print(f"\n🌊 LAUNCHING WAVE: {actual} × {task_type.upper()} agents")
        print(f"   Model: {self.config.model}")
        print(f"   YOLO: {'ON' if self.config.yolo_mode else 'OFF'}")
        
        results = []
        batch_size = self.config.parallel_batches
        
        for batch_start in range(0, actual, batch_size):
            batch_end = min(batch_start + batch_size, actual)
            batch_count = batch_end - batch_start
            
            print(f"   Batch {batch_start//batch_size + 1}: {batch_count} agents...")
            
            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                futures = {}
                for i in range(batch_count):
                    agent_id = f"{task_type}_{len(self.completed_agents) + i}"
                    future = executor.submit(self._run_agent, agent_id, task_type, context)
                    futures[future] = agent_id
                
                for future in as_completed(futures):
                    agent_id = futures[future]
                    try:
                        result = future.result()
                        with self._lock:
                            self.completed_agents.append(result)
                            results.append(result)
                        self._print_agent_done(agent_id, result)
                    except Exception as e:
                        print(f"   ❌ Agent {agent_id} failed: {e}")
            
            # Save state between batches
            save_state(self.loop, f"swarm_state_{task_type}.json")
        
        return results
    
    def launch_full_swarm(self, max_agents: int = 400):
        """Launch the full 400-agent swarm across all task types."""
        print(f"\n{'#'*60}")
        print(f"🐝 400-AGENT SWARM LAUNCH")
        print(f"{'#'*60}")
        print(f"  Project: {self.project.name}")
        print(f"  Description: {self.project.description}")
        print(f"  Goal: {self.project.goal}")
        print(f"  Model: {self.config.model}")
        print(f"  Total agents: {max_agents}")
        print(f"  YOLO: {'⚠️ ON' if self.config.yolo_mode else 'normal'}")
        print(f"{'#'*60}\n")
        
        # Phase 1: Architecture & Planning (40 agents)
        print(f"\n{'─'*50}")
        print(f"📐 PHASE 1: ARCHITECTURE & PLANNING — 40 agents")
        print(f"{'─'*50}")
        arch_results = self.launch_wave(40, "architecture", {
            "phase": "planning",
            "project": self.project.name,
            "description": self.project.description,
            "goal": self.project.goal,
        })
        
        # Phase 2: Code Generation (200 agents)
        print(f"\n{'─'*50}")
        print(f"💻 PHASE 2: CODE GENERATION — 200 agents")
        print(f"{'─'*50}")
        code_results = self.launch_wave(200, "codegen", {
            "phase": "implementation",
            "architecture": arch_results,
            "project": self.project.name,
        })
        
        # Phase 3: Security Audit (40 agents)
        print(f"\n{'─'*50}")
        print(f"🔒 PHASE 3: SECURITY AUDIT — 40 agents")
        print(f"{'─'*50}")
        security_results = self.launch_wave(40, "security", {
            "phase": "security",
            "code": code_results,
        })
        
        # Phase 4: Bug Hunting (40 agents)
        print(f"\n{'─'*50}")
        print(f"🐛 PHASE 4: BUG HUNTING — 40 agents")
        print(f"{'─'*50}")
        bug_results = self.launch_wave(40, "bug_hunt", {
            "phase": "testing",
            "code": code_results,
            "security": security_results,
        })
        
        # Phase 5: Review & Polish (40 agents)
        print(f"\n{'─'*50}")
        print(f"✨ PHASE 5: REVIEW & POLISH — 40 agents")
        print(f"{'─'*50}")
        review_results = self.launch_wave(40, "review", {
            "phase": "polish",
            "code": code_results,
        })
        
        # Phase 6: Documentation (40 agents)
        print(f"\n{'─'*50}")
        print(f"📝 PHASE 6: DOCUMENTATION — 40 agents")
        print(f"{'─'*50}")
        docs_results = self.launch_wave(40, "docs", {
            "phase": "documentation",
            "project": self.project.name,
            "code": code_results,
        })
        
        print(f"\n{'★'*60}")
        print(f"🏁 400-AGENT SWARM COMPLETE")
        print(f"   Total agents completed: {len(self.completed_agents)}")
        print(f"{'★'*60}")
        
        return {
            "architecture": arch_results,
            "code": code_results,
            "security": security_results,
            "bugs": bug_results,
            "review": review_results,
            "docs": docs_results,
            "total_agents": len(self.completed_agents),
        }
    
    def _run_agent(self, agent_id: str, task_type: str, context: dict) -> dict:
        """Run a single agent task."""
        # Simulated agent run — in production, this delegates to Hermes/DeepSeek
        time.sleep(0.1)  # Simulate work
        return {
            "agent_id": agent_id,
            "task_type": task_type,
            "status": "completed",
            "result": f"Agent {agent_id} completed {task_type} task",
        }
    
    def _print_agent_done(self, agent_id: str, result: dict):
        total = len(self.completed_agents)
        print(f"   ✅ [{total}/400] {agent_id} — {result.get('status', 'done')}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Hermes Swarm Loop — 400-Agent Launcher")
    parser.add_argument("--name", "-n", required=True, help="Project name")
    parser.add_argument("--desc", "-d", required=True, help="Project description")
    parser.add_argument("--goal", "-g", help="Project goal")
    parser.add_argument("--model", "-m", default="deepseek-v4-flash", 
                       help="Agent model (deepseek-v4-flash, claude-sonnet-4, gpt-5, etc.)")
    parser.add_argument("--agents", type=int, default=400, help="Number of agents")
    parser.add_argument("--yolo", action="store_true", default=True, help="YOLO mode")
    parser.add_argument("--workdir", default=".", help="Working directory")
    
    args = parser.parse_args()
    
    project = ProjectContext(
        name=args.name,
        description=args.desc,
        workdir=Path(args.workdir),
        goal=args.goal or args.desc,
    )
    
    config = SwarmConfig(
        max_agents=args.agents,
        model=args.model,
        yolo_mode=args.yolo,
    )
    
    swarm = Swarm400(project=project, config=config)
    results = swarm.launch_full_swarm(max_agents=args.agents)
    
    # Save final state
    final_state = {
        "project": project.name,
        "total_agents": results["total_agents"],
        "phases": {k: len(v) for k, v in results.items() if isinstance(v, list)},
        "status": "completed",
    }
    with open("swarm_400_complete.json", "w") as f:
        json.dump(final_state, f, indent=2)
    
    print(f"\n💾 Final state saved to swarm_400_complete.json")


if __name__ == "__main__":
    main()
