#!/usr/bin/env python3
"""
orchestrator.py — Hermes-as-Orchestrator (v2)
=============================================
This module provides CONVENIENCE FUNCTIONS for ME (Hermes Agent) to call
as the orchestrator. NOT a standalone runner — I drive the pipeline step
by step using my tools.

Key concept: I (Hermes) am the orchestrator. This module gives me:
1. Swarm command generation (via bootstrap)
2. State tracking helpers
3. Point completion detection
4. Blocked worker recovery

Usage (from my tool calls — NOT as a subprocess):
  from engine.orchestrator import bootstrap_swarm, check_point_done, recover_blocked_workers
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SWARM_DIR = HERE.parent


def run(cmd, timeout=30, cwd=None):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        return r.stdout.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]", -1
    except Exception as e:
        return f"[ERROR {e}]", -1


def bootstrap_swarm(
    project_name="UltraSales",
    project_desc="",
    project_dir="/opt/email-platform",
    phase="development",
    yolo_zone="staging",
    max_agents=22,
    db_path=None,
    add_websearch=False,
):
    """
    Run bootstrap.py to generate swarm commands for a phase.
    Returns the launch config dict with commands.
    """
    cmd = (
        f'cd {SWARM_DIR} && python3 bootstrap.py '
        f'--project-name "{project_name}" '
        f'--project-desc "{project_desc}" '
        f'--project-dir "{project_dir}" '
        f'--phase {phase} '
        f'--yolo-zone {yolo_zone} '
        f'--max-agents {max_agents}'
    )
    if db_path:
        cmd += f' --db-path "{db_path}"'

    out, code = run(cmd, timeout=30)
    if code != 0:
        print(f"Bootstrap failed: {out[:300]}")
        return None

    # Read the launch config
    launch_path = SWARM_DIR / ".hermes_swarm_launch.json"
    if not launch_path.exists():
        print(f"No launch config at {launch_path}")
        return None

    with open(launch_path) as f:
        config = json.load(f)

    # Optionally add websearch to goals
    if add_websearch:
        web_note = (
            "WEBSEARCH AVAILABLE: Use web_search tool if you need to check "
            "official documentation, APIs, or best practices for your task."
        )
        for i in range(len(config["commands"])):
            config["commands"][i] = config["commands"][i].replace(
                ". CRITICAL", f". {web_note} CRITICAL"
            )

    return config


def execute_swarm_command(command_str, timeout=60):
    """
    Execute a single hermes kanban swarm command.
    Returns (success, output).
    """
    print(f"  Executing swarm command...")
    out, code = run(command_str, timeout=timeout)
    if code != 0:
        print(f"  Swarm command failed (exit {code}): {out[:200]}")
        return False, out
    print(f"  Swarm created: {out[:200]}")
    return True, out


def count_agents(phase, point, project_name="UltraSales"):
    """Count agent statuses for a point in a phase."""
    kanban_file = "/tmp/kanban_list.json"
    out, code = run(f"hermes kanban list --json 2>/dev/null > {kanban_file}", timeout=15)
    if code != 0:
        return {"total": 0, "done": 0, "running": 0, "blocked": 0, "ready": 0, "todo": 0}
    
    try:
        with open(kanban_file) as f:
            tasks = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"total": 0, "done": 0, "running": 0, "blocked": 0, "ready": 0, "todo": 0}
    
    keyword = f"{project_name} — {phase} — {point}"
    matching = [t for t in tasks if keyword in t.get("title", "")]
    
    result = {"total": len(matching)}
    for s in ["done", "running", "todo", "ready", "blocked"]:
        result[s] = sum(1 for t in matching if t.get("status") == s)
    return result


def check_point_done(phase, point, expected_agents=22, project_name="UltraSales"):
    """
    Check if a point is fully complete (all agents + verifier + synthesizer).
    Returns (is_done, status_dict).
    """
    s = count_agents(phase, point, project_name)
    total_expected = expected_agents + 2  # workers + verifier + synth (root is separate)
    
    # Also check verifier/synth by looking for any remaining "todo" tasks
    kanban_file = "/tmp/kanban_list.json"
    if os.path.exists(kanban_file):
        try:
            with open(kanban_file) as f:
                tasks = json.load(f)
            # Root task for this swarm
            root_keyword = f"Swarm: Work on point '{point}' of phase '{phase}'"
            swarm_tasks = [t for t in tasks if root_keyword in t.get("title", "")]
            
            # Verifier + synth for this swarm
            swarm_root_ids = [t["id"] for t in swarm_tasks]
            # Gather all tasks that belong to these swarms
            point_tasks = [t for t in tasks if keyword_in_swarm(t, swarm_root_ids)]
            
            remaining = len([t for t in point_tasks if t.get("status") in ("todo", "ready")])
            is_done = remaining == 0 and s["blocked"] == 0
        except:
            is_done = s["done"] >= total_expected and s["running"] == 0 and s["blocked"] == 0
    else:
        is_done = s["done"] >= total_expected and s["running"] == 0 and s["blocked"] == 0
    
    return is_done, s


def keyword_in_swarm(task, swarm_root_ids):
    """Check if a task belongs to a swarm by parent chain."""
    parents = task.get("parents", [])
    if isinstance(parents, list):
        return any(p in swarm_root_ids for p in parents)
    return parents in swarm_root_ids


def recover_blocked_workers(phase, point, project_name="UltraSales"):
    """
    Find and unblock any blocked workers for this point.
    Returns number of workers recovered.
    """
    kanban_file = "/tmp/kanban_list.json"
    if not os.path.exists(kanban_file):
        run("hermes kanban list --json 2>/dev/null > /tmp/kanban_list.json", timeout=15)
    
    try:
        with open(kanban_file) as f:
            tasks = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return 0
    
    keyword = f"{project_name} — {phase} — {point}"
    blocked = [t for t in tasks if keyword in t.get("title", "") and t.get("status") == "blocked"]
    
    recovered = 0
    for t in blocked:
        tid = t["id"]
        run(f"hermes kanban unblock {tid} 2>/dev/null", timeout=10)
        run("hermes kanban dispatch --max 1 2>/dev/null", timeout=10)
        print(f"  Unblocked: {t['title'][:50]}")
        recovered += 1
    
    return recovered


def get_verifier_synth_id(swarm_root_id):
    """Find verifier and synthesizer task IDs for a swarm root."""
    kanban_file = "/tmp/kanban_list.json"
    try:
        with open(kanban_file) as f:
            tasks = json.load(f)
    except:
        return None, None
    
    verifier = None
    synth = None
    for t in tasks:
        parents = t.get("parents", [])
        if isinstance(parents, list):
            if swarm_root_id in parents:
                if "Verify" in t.get("title", ""):
                    verifier = t["id"]
                elif "Synthesize" in t.get("title", ""):
                    synth = t["id"]
    
    return verifier, synth


def poll_until_done(phase, point, expected_agents=22, project_name="UltraSales", 
                    max_wait=1800, poll_interval=60, on_blocked_callback=None):
    """
    Poll until a point is completely done or timeout.
    Returns True if complete.
    """
    start = time.time()
    last_check = ""
    
    while time.time() - start < max_wait:
        # Dump kanban list once per poll cycle
        run("hermes kanban list --json 2>/dev/null > /tmp/kanban_list.json", timeout=15)
        
        is_done, s = check_point_done(phase, point, expected_agents, project_name)
        
        status_line = f"  {s['done']} done | {s['running']} running | {s['blocked']} blocked | {s['ready']} ready"
        if status_line != last_check:
            print(status_line)
            last_check = status_line
        
        if is_done:
            print(f"  ✅ Point '{point}' complete!")
            return True
        
        # Recover blocked
        if s.get("blocked", 0) > 0:
            recovered = recover_blocked_workers(phase, point, project_name)
            if recovered > 0 and on_blocked_callback:
                on_blocked_callback(recovered)
        
        time.sleep(poll_interval)
    
    print(f"  ❌ TIMEOUT after {max_wait}s for point '{point}'")
    return False
