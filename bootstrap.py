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
import subprocess
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
        errors.append(f"Python 3.10+ required (got {sys.version_info.major}.{sys.version_info.minor})")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Hermes Swarm Loop — Bootstrap Launcher")
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--project-desc", default="")
    parser.add_argument("--phase", default="development", choices=PhaseMachine.ALL_PHASES)
    parser.add_argument("--yolo-zone", default="test", choices=list(YOLO_ZONES.keys()))
    parser.add_argument("--max-agents", type=int, default=11)
    parser.add_argument("--init-only", action="store_true")
    parser.add_argument("--db-path", default=None)
    args = parser.parse_args()

    swarm_dir = str(_HERE)
    print(f"Hermes Swarm Loop — Bootstrap")
    print(f"  Project: {args.project_name}  Phase: {args.phase}")
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
    for pt in points:
        pt_m.create_point(args.phase, pt, args.max_agents)
    print(f"  Phase '{args.phase}': {len(points)} points")

    # Stage 4
    print("\n--- Stage 4: YOLO Init ---")
    ym = YOLOMachine(db)
    capped = min(args.max_agents, YOLO_ZONES[args.yolo_zone]["max_parallel"])
    ym.set_zone(args.yolo_zone)
    ym.reset_safety_valve()
    print(f"  Zone: {args.yolo_zone} (capped at {capped})")

    # Stage 5
    print("\n--- Stage 5: Launch ---")
    launch = {
        "project_name": args.project_name,
        "project_desc": args.project_desc,
        "phase": args.phase,
        "max_agents": capped,
        "swarm_dir": swarm_dir,
        "points": points,
        "commands": [
            f"hermes kanban swarm --name \"{args.project_name} — {args.phase}: {pt}\" "
            f"--description \"{args.project_desc}\" --workdir \"{swarm_dir}\" "
            f"--max-workers {capped} --phase {args.phase} --point {pt}"
            for pt in points
        ],
    }
    json_path = os.path.join(swarm_dir, ".hermes_swarm_launch.json")
    with open(json_path, "w") as f:
        json.dump(launch, f, indent=2)

    if not args.init_only:
        for i, cmd in enumerate(launch["commands"], 1):
            print(f"  [{i}] {cmd}")
    print(f"\n  Config saved to {json_path}")
    print("\nDone. Get shit done.")


if __name__ == "__main__":
    main()
