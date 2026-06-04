#!/usr/bin/env python3
"""UltraSales Full Pipeline — automated Phase 0→1→2→3→Gate→Loop"""
import json, os, shutil, subprocess, sys, time
from pathlib import Path

SWARM_DIR = Path("/root/code/hermes-swarm-loop")
PROJECT = "UltraSales"
DESC = "Build unified Sales & Marketing OS at /opt/email-platform/. 12+ modules: Content CMS with copywriter AI, Unified Email Inbox (ProtonMail clone), Ad Suites (Google, YouTube, X, TikTok, Meta), Social Suite (posting+replies), BullGPT Analytics, Voice AI (ElevenLabs+Vapi+DeepSeek), Lead Scraper, CRM Kanban, Micro-Budget Engine, Workflow Automation. White shadcn/ui theme applied. Read /opt/email-platform/PRD.md. Competitive analysis in arch/competitive-analysis.md."

PHASES = {
    "prd_build": {"points": ["build"], "agents": 33, "skill": "kanban-worker,hermes-swarm-loop"},
    "development": {"points": ["architecture", "setup", "code_generation"], "agents": 11, "skill": "kanban-worker,hermes-swarm-loop"},
    "hunting": {"points": ["bugs", "architecture_review", "security"], "agents": 11, "skill": "kanban-worker,hermes-swarm-loop"},
    "quality": {"points": ["audit", "improve", "review"], "agents": 11, "skill": "kanban-worker,hermes-swarm-loop"},
}

def run_cmd(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout
    except subprocess.TimeoutExpired:
        return f"[TIMEOUT {timeout}s]"
    except Exception as e:
        return f"[ERROR {e}]"

def count_kanban(keyword="UltraSales"):
    out = run_cmd("hermes kanban list --json 2>/dev/null", timeout=15)
    try:
        data = json.loads(out)
        matching = [t for t in data if keyword in t.get("title", "")]
        done = sum(1 for t in matching if t.get("status") == "done")
        running = sum(1 for t in matching if t.get("status") == "running")
        ready = sum(1 for t in matching if t.get("status") == "ready")
        blocked = sum(1 for t in matching if t.get("status") == "blocked")
        return {"done": done, "running": running, "ready": ready, "blocked": blocked, "total": len(matching)}
    except:
        return {"done": 0, "running": 0, "ready": 0, "blocked": 0, "total": 0}

def wait_for_point(phase, point, expected=11, max_wait=3600):
    """Wait for all workers in a point to complete."""
    keyword = f"{PROJECT} — {phase}"
    start = time.time()
    while time.time() - start < max_wait:
        s = count_kanban(keyword)
        print(f"  [{phase}:{point}] D:{s['done']} R:{s['running']} Y:{s['ready']} B:{s['blocked']}")
        if s["done"] >= expected:
            if expected == 11:
                # Check verifier + synthesizer too
                out = run_cmd("hermes kanban list --json 2>/dev/null", timeout=15)
                try:
                    data = json.loads(out)
                    total_done = sum(1 for t in data if keyword in t.get("title", "") and t.get("status") == "done")
                    if total_done >= expected + 2:  # workers + verifier + synthesizer = 13
                        return True
                except:
                    pass
            return True
        # Handle blocked workers
        if s.get("blocked", 0) > 0:
            out = run_cmd("hermes kanban list --json 2>/dev/null", timeout=15)
            try:
                data = json.loads(out)
                for t in data:
                    if t.get("status") == "blocked" and keyword in t.get("title", ""):
                        run_cmd(f"hermes kanban unblock {t['id']} 2>/dev/null", timeout=10)
                        run_cmd("hermes kanban dispatch --max 1 2>/dev/null", timeout=10)
                        print(f"  Unblocked {t['id']}")
            except:
                pass
        time.sleep(60)
    return False

def bootstrap_phase(phase, agents):
    """Run bootstrap.py and execute the swarm command."""
    # Clean swarm state for fresh phase
    os.chdir(str(SWARM_DIR))
    for f in [".swarm_state.db", ".hermes_swarm_launch.json"]:
        p = SWARM_DIR / f
        if p.exists():
            p.unlink()
    
    cmd = f'python3 bootstrap.py --project-name "{PROJECT}" --project-desc "{DESC}" --phase {phase} --yolo-zone production --max-agents {agents} 2>&1'
    out = run_cmd(cmd, timeout=30)
    print(f"Bootstrap {phase}: {out[:200]}")
    
    # Execute the swarm command from launch config
    cfg_path = SWARM_DIR / ".hermes_swarm_launch.json"
    if cfg_path.exists():
        with open(cfg_path) as f:
            cfg = json.load(f)
        for cmd in cfg["commands"]:
            print(f"Running: {cmd[:120]}...")
            out = run_cmd(cmd, timeout=30)
            print(f"  {out[:200]}")
            # Wait for this point's workers to complete
            for pt in cfg["points"]:
                expected = min(agents, PHASES[phase]["agents"])
                if not wait_for_point(phase, pt, expected=max(11, expected)):
                    print(f"  TIMEOUT on {phase}:{pt}")
                    return False
            return True
    return False

# ===== MAIN PIPELINE =====
print("=" * 60)
print("ULTRASALES — FULL AUTOMATED PIPELINE")
print("Phase 0: PRD BUILD (33 agents)")
print("Phase 1: DEVELOPMENT (33 agents — ARCH→SETUP→CODE)")
print("Phase 2: HUNTING (33 agents — BUGS→ARCH REVIEW→SECURITY)")
print("Phase 3: QUALITY (33 agents — AUDIT→IMPROVE→REVIEW)")
print("Loop: Phase 2→3→Mastery Gate until PASS")
print("YOLO: ON — zero questions, zero approval")
print("=" * 60)

# Phase 0: PRD BUILD
print("\n>>> PHASE 0: PRD BUILD <<<")
bootstrap_phase("prd_build", 33)

# Phase 1: DEVELOPMENT (once)
print("\n>>> PHASE 1: DEVELOPMENT <<<")
bootstrap_phase("development", 33)

# Phase 2→3 Loop
loop_count = 0
while True:
    loop_count += 1
    print(f"\n{'='*60}")
    print(f">>> LOOP {loop_count}: PHASE 2 HUNTING <<<")
    bootstrap_phase("hunting", 33)
    
    print(f"\n>>> LOOP {loop_count}: PHASE 3 QUALITY <<<")
    bootstrap_phase("quality", 33)
    
    print(f"\n>>> LOOP {loop_count}: MASTERY GATE <<<")
    # Run mastery gate via hermes chat
    gate_cmd = f'hermes chat -q "Load hermes-swarm-loop skill and execute Mastery Gate for project {PROJECT} at /opt/email-platform/. Score all 7 dimensions. Report PASS/BLOCK." 2>&1'
    gate_out = run_cmd(gate_cmd, timeout=300)
    print(f"Gate: {gate_out[:300]}")
    
    if "PASS" in gate_out or "passed" in gate_out.lower():
        print(f"\n>>> MASTERY GATE PASSED after {loop_count} loop(s) <<<")
        break
    
    if "BLOCK" in gate_out or "block" in gate_out.lower():
        print(f"\n>>> MASTERY GATE BLOCKED — continuing loop {loop_count + 1} <<<")
        continue

print("\n" + "=" * 60)
print("PIPELINE COMPLETE")
print("=" * 60)
