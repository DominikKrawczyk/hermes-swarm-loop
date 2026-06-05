#!/usr/bin/env python3
"""
bootstrap.py — Hermes Swarm Loop 5-Stage Launcher
===================================================
5-Stage Pipeline:
  1. Environment Check  — verifies hermes, python3, gh, git on PATH
  2. Database Init      — creates .swarm_state.db with WAL + 5 tables
  3. Phase Setup        — writes phase + point records
  4. YOLO Init          — configures YOLO zone and caps
  5. Launch             — prints kanban swarm commands, saves config

Usage:
  python3 bootstrap.py --project-name "MyApp" --project-desc "Build X"
  python3 bootstrap.py --phase prd_build --yolo-zone staging --max-agents 66
  python3 bootstrap.py --init-only
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from engine.state_machine import (
    StateDB, PhaseMachine, PointMachine, YOLOMachine, YOLO_ZONES,
)


def check_env():
    errors = []
    for cmd, name in [("hermes","Hermes Agent"), ("python3","Python"), ("gh","GitHub CLI"), ("git","Git")]:
        if not shutil.which(cmd):
            errors.append(f"Missing: {name} ({cmd})")
    if sys.version_info < (3, 10):
        errors.append(f"Python 3.10+ required (got {sys.version_info[0]}.{sys.version_info[1]})")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Hermes Swarm Loop — Bootstrap Launcher")
    parser.add_argument("--project-name", default="")
    parser.add_argument("--project-desc", default="")
    parser.add_argument("--project-dir", default="", help="Absolute path to project directory for persistent agent output")
    parser.add_argument("--phase", default="development", choices=PhaseMachine.ALL_PHASES)
    parser.add_argument("--yolo-zone", default="test", choices=list(YOLO_ZONES.keys()))
    parser.add_argument("--max-agents", type=int, default=22)
    parser.add_argument("--init-only", action="store_true")
    parser.add_argument("--db-path", default=None)
    parser.add_argument("--websearch", action="store_true",
        help="Add web_search capability note to agent goals")
    parser.add_argument("--git-push", action="store_true",
        help="Auto-push to GitHub after bootstrap")
    args = parser.parse_args()

    if not args.init_only and not args.project_name:
        parser.error("--project-name is required (use --init-only to skip)")

    swarm_dir = str(_HERE)
    print("Hermes Swarm Loop — Bootstrap")
    print(f"  Project: {args.project_name or '(init-only)'}  Phase: {args.phase}")
    print(f"  YOLO: {args.yolo_zone}  Agents: {args.max_agents}")

    # Stage 1
    print("\n--- Stage 1: Environment Check ---")
    env_errors = check_env()
    if env_errors:
        for e in env_errors:
            print(f"  {e}")
        sys.exit(1)
    print("  OK")

    # Stage 2
    print("\n--- Stage 2: Database Init ---")
    db_path = args.db_path or os.path.join(swarm_dir, ".swarm_state.db")
    db = StateDB(db_path)
    print(f"  DB: {db_path}")

    # Stage 3
    print("\n--- Stage 3: Phase Setup ---")
    pm = PhaseMachine(db)
    pm.start_phase(args.phase)
    pt_m = PointMachine(db)
    points = PhaseMachine.POINTS.get(args.phase, [])
    capped = min(args.max_agents, YOLO_ZONES[args.yolo_zone]["max_parallel"])
    for pt in points:
        pt_m.create_point(args.phase, pt, capped)
    print(f"  Phase '{args.phase}': {len(points)} points (agents capped at {capped})")

    # Stage 4
    print("\n--- Stage 4: YOLO Init ---")
    ym = YOLOMachine(db)
    ym.set_zone(args.yolo_zone)
    ym.reset_safety_valve()
    print(f"  Zone: {args.yolo_zone} (capped at {capped})")
    # Update max_agents to capped so create_point uses the YOLO-compliant count
    args.max_agents = capped

    # Stage 5
    print("\n--- Stage 5: Launch ---")
    
    worker_skill = "kanban-worker,hermes-swarm-loop"
    verifier = "default"
    synthesizer = "default"
    
    commands = []
    for pt in points:
        workers = " ".join([
            f'--worker default:"{args.project_name} — {args.phase} — {pt}_Agent{i+1:02d}:{worker_skill}"'
            for i in range(capped)
        ])
        project_dir = args.project_dir or "/opt/email-platform"
        persistence_warning = (
            f"CRITICAL — PERSISTENCE: Your scratch workspace is TEMPORARY and will be DELETED. "
            f"Write ALL files directly to {project_dir}/ or your work is LOST. "
            f"Never write to ~/.hermes/kanban/workspaces/."
        )
        web_note = ""
        if args.websearch:
            web_note = (
                "WEBSEARCH/TOOL ACCESS: You have web_search and terminal tools available. "
                f"Use them to check official docs, APIs, frameworks, and best practices. "
                f"Research before writing — don't guess API signatures."
            )
        extra = f" {web_note}" if web_note else ""
        safety = (
            "CRITICAL — SAFETY: NEVER delete, remove, or overwrite existing files. "
            "ONLY modify existing files or create NEW files. "
            "Do NOT remove imports, models, routes, or workers — they may be used by other modules. "
            "If you think a file is dead code, add a comment '# TODO: verify if still needed' "
            "instead of deleting it. "
            "BREAKING THIS RULE CORRUPTS THE PROJECT."
        )
        goal = f"Work on point '{pt}' of phase '{args.phase}' for project '{args.project_name}'. {args.project_desc}.{extra} {persistence_warning} {safety}"
        cmd = f"hermes kanban swarm {workers} --verifier {verifier} --synthesizer {synthesizer} \"{goal}\""
        commands.append(cmd)
    
    launch = {
        "project_name": args.project_name,
        "project_desc": args.project_desc,
        "phase": args.phase,
        "max_agents": capped,
        "swarm_dir": swarm_dir,
        "points": points,
        "worker_skill": worker_skill,
        "verifier": verifier,
        "synthesizer": synthesizer,
        "commands": commands,
    }
    json_path = os.path.join(swarm_dir, ".hermes_swarm_launch.json")
    with open(json_path, "w") as f:
        json.dump(launch, f, indent=2)

    if not args.init_only:
        for i, cmd in enumerate(launch["commands"], 1):
            print(f"  [{i}] {cmd}")
    print(f"\n  Config saved to {json_path}")
    
    # Git push if requested
    if args.git_push and not args.init_only:
        try:
            from engine.git_push import push_framework
            push_framework(message=f"Bootstrap phase '{args.phase}' for {args.project_name}")
        except ImportError:
            print("  ⚠️ git_push module not available, skipping git push")
    
    print("\nDone. Get shit done.")


if __name__ == "__main__":
    main()
