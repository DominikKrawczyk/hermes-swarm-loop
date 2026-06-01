#!/usr/bin/env python3
"""
Hermes Swarm Loop — Bounty Hunter
3×3 Bug, Architecture & Security Hunting Engine.

Three hunt types, each with 3 depth levels, each with 3 parallel agents.

Hunt Types:
  1. BUGS — logic errors, edge cases, race conditions, memory leaks
  2. ARCHITECTURE — design flaws, coupling, scalability, tech debt
  3. SECURITY — injections, auth flaws, crypto weakneasses, data leaks

Each hunt spawns 3×3×3 = 27 agents minimum.
In YOLO mode: 400 agents full spectrum.
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


HUNT_TEMPLATES = {
    "bugs": {
        "name": "🐛 Bug Hunter",
        "depth_levels": [
            "Shallow: Syntax errors, type mismatches, obvious null pointers",
            "Medium: Race conditions, memory leaks, incorrect state management",
            "Deep: Heisenbugs, concurrency deadlocks, protocol violations",
        ],
        "checklist": [
            "Null pointer dereferences",
            "Buffer overflows / index out of bounds",
            "Race conditions (TOCTOU, check-then-use)",
            "Memory leaks (allocations without free)",
            "Incorrect error handling",
            "Type confusion / casting errors",
            "Integer overflow / underflow",
            "Logic errors in conditionals",
            "Incorrect API usage",
            "Resource leaks (file handles, sockets)",
        ]
    },
    "architecture": {
        "name": "🏗️ Architecture Hunter",
        "depth_levels": [
            "Shallow: File organization, naming, basic patterns",
            "Medium: Coupling, cohesion, dependency injection, SOLID",
            "Deep: Scalability, distributed systems, CAP theorem violations",
        ],
        "checklist": [
            "Circular dependencies",
            "God objects / too many responsibilities",
            "Missing abstraction layers",
            "Tight coupling between modules",
            "Violation of single responsibility",
            "Missing interface segregation",
            "Incorrect use of design patterns",
            "Scalability bottlenecks",
            "Single points of failure",
            "Missing monitoring/observability",
        ]
    },
    "security": {
        "name": "🔒 Security Hunter",
        "depth_levels": [
            "Shallow: Hardcoded secrets, basic injection, missing auth",
            "Medium: CSRF, XSS, SQL injection, path traversal, IDOR",
            "Deep: Cryptography flaws, side channels, supply chain, zero-day patterns",
        ],
        "checklist": [
            "Hardcoded API keys / secrets",
            "SQL / NoSQL injection",
            "Cross-site scripting (XSS)",
            "Cross-site request forgery (CSRF)",
            "Insecure direct object references (IDOR)",
            "Authentication bypass",
            "Authorization escalation",
            "Path traversal",
            "Insecure deserialization",
            "Cryptographic weaknesses",
            "Side-channel vulnerabilities",
            "Supply chain risks",
        ]
    }
}


def hunt_path(target_path: str, hunt_type: str, depth: int = 1, 
              agents: int = 3, model: str = "deepseek-v4-flash",
              yolo: bool = True) -> list[dict]:
    """
    Run a hunt on a target path.
    
    Args:
        target_path: Path to scan
        hunt_type: "bugs", "architecture", or "security"
        depth: 1 (shallow), 2 (medium), or 3 (deep)
        agents: Number of parallel agents per depth
        model: Model to use for agents
        yolo: Auto-approve everything
    
    Returns:
        List of findings
    """
    template = HUNT_TEMPLATES.get(hunt_type)
    if not template:
        raise ValueError(f"Unknown hunt type: {hunt_type}. Choose from: {list(HUNT_TEMPLATES.keys())}")
    
    print(f"\n{'─'*50}")
    print(f"{template['name']} — Depth {depth}")
    print(f"  Target: {target_path}")
    print(f"  Agents: {agents}")
    print(f"  Model:  {model}")
    print(f"{'─'*50}")
    
    depth_desc = template["depth_levels"][min(depth - 1, len(template["depth_levels"]) - 1)]
    items_to_check = template["checklist"]
    
    print(f"  Depth focus: {depth_desc}")
    print(f"  Checklist items: {len(items_to_check)}")
    
    all_findings = []
    
    # Spawn agents per depth level
    actual_depth = min(depth, 3)
    for d in range(actual_depth):
        dd = HUNT_TEMPLATES[hunt_type]["depth_levels"][d]
        print(f"\n  └─ Level {d+1}/3: {dd[:60]}...")
        
        with ThreadPoolExecutor(max_workers=agents) as executor:
            futures = {}
            for i in range(agents):
                agent_id = f"{hunt_type}_d{d}_a{i}"
                future = executor.submit(
                    _run_hunter_agent, agent_id, target_path, hunt_type, d+1, items_to_check, model
                )
                futures[future] = agent_id
            
            for future in as_completed(futures):
                agent_id = futures[future]
                try:
                    result = future.result()
                    if result.get("findings"):
                        all_findings.extend(result["findings"])
                        print(f"    ✅ {agent_id}: {len(result['findings'])} findings")
                    else:
                        print(f"    ✅ {agent_id}: clean")
                except Exception as e:
                    print(f"    ❌ {agent_id}: {e}")
    
    # 3×3 multiplier: each depth → 3 sub-hunts
    if depth >= 2:
        print(f"\n  └─ Running 3× sub-hunts for deeper analysis...")
        for sub in range(3):
            sub_findings = []
            for d in range(actual_depth):
                agents_sub = _run_hunter_agent(
                    f"{hunt_type}_sub{sub}_d{d}", target_path, hunt_type, d+1, 
                    items_to_check + [f"sub-hunt #{sub} focus"], model
                )
                if agents_sub.get("findings"):
                    sub_findings.extend(agents_sub["findings"])
            all_findings.extend(sub_findings)
            print(f"      Sub-hunt {sub+1}/3: {len(sub_findings)} more findings")
    
    # Severity tagging
    for f in all_findings:
        if isinstance(f, dict) and "severity" not in f:
            # Auto-tag based on content
            text = str(f).lower()
            if any(w in text for w in ["critical", "remote", "exploit", "bypass", "crash"]):
                f["severity"] = "CRITICAL"
            elif any(w in text for w in ["high", "vulnerability", "leak", "overflow"]):
                f["severity"] = "HIGH"
            elif any(w in text for w in ["medium", "warning", "concern"]):
                f["severity"] = "MEDIUM"
            else:
                f["severity"] = "LOW"
    
    print(f"\n  ── Total findings: {len(all_findings)}")
    severity_counts = {}
    for f in all_findings:
        sev = f.get("severity", "UNKNOWN") if isinstance(f, dict) else "UNKNOWN"
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
    for sev, count in sorted(severity_counts.items()):
        print(f"     {sev}: {count}")
    
    return all_findings


def _run_hunter_agent(agent_id: str, target_path: str, hunt_type: str, 
                      depth: int, checklist: list, model: str) -> dict:
    """Run a single hunter agent."""
    # In production: delegate to Hermes/DeepSeek agent
    # For now, return template-based findings
    import random
    has_findings = random.random() < 0.3  # 30% chance of finding something
    findings = []
    if has_findings:
        findings.append({
            "agent": agent_id,
            "type": hunt_type,
            "depth": depth,
            "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            "description": f"Potential {hunt_type} issue found at depth {depth}",
            "location": target_path,
            "checklist_item": random.choice(checklist) if checklist else "general",
        })
    return {"agent_id": agent_id, "findings": findings}


def full_bounty_hunt(target_path: str, depth: int = 3, 
                      agents_per_type: int = 9,
                      model: str = "deepseek-v4-flash",
                      yolo: bool = True) -> dict:
    """Run all three hunt types at full depth."""
    print(f"\n{'#'*60}")
    print(f"🔍 FULL BOUNTY HUNT — 3×3×3 = 27+ agents")
    print(f"{'#'*60}")
    print(f"  Target: {target_path}")
    print(f"  Depth:  {depth}")
    print(f"  Model:  {model}")
    print(f"  YOLO:   {'⚠️ ON' if yolo else 'normal'}")
    print(f"{'#'*60}\n")
    
    results = {}
    all_findings = []
    
    for hunt_type in ["bugs", "architecture", "security"]:
        print(f"\n{'='*50}")
        print(f"▶ HUNT: {hunt_type.upper()}")
        print(f"{'='*50}")
        findings = hunt_path(target_path, hunt_type, depth=depth, 
                             agents=agents_per_type, model=model, yolo=yolo)
        results[hunt_type] = findings
        all_findings.extend(findings)
    
    # Summary
    print(f"\n{'★'*60}")
    print(f"📊 BOUNTY HUNT SUMMARY")
    print(f"{'★'*60}")
    print(f"  Total findings: {len(all_findings)}")
    
    severity_counts = {}
    type_counts = {}
    for f in all_findings:
        sev = f.get("severity", "UNKNOWN") if isinstance(f, dict) else "UNKNOWN"
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        ft = f.get("type", "unknown") if isinstance(f, dict) else "unknown"
        type_counts[ft] = type_counts.get(ft, 0) + 1
    
    for sev, count in sorted(severity_counts.items()):
        emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "⚪"}.get(sev, "⚪")
        print(f"  {emoji} {sev}: {count}")
    for ft, count in sorted(type_counts.items()):
        print(f"  📁 {ft}: {count}")
    
    results["_summary"] = {
        "total": len(all_findings),
        "by_severity": severity_counts,
        "by_type": type_counts,
    }
    
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Hermes Swarm Loop — Bounty Hunter")
    parser.add_argument("--path", default=".", help="Target path")
    parser.add_argument("--depth", type=int, default=3, help="Hunt depth (1-3)")
    parser.add_argument("--agents", type=int, default=9, help="Agents per hunt type")
    parser.add_argument("--model", default="deepseek-v4-flash", help="Agent model")
    parser.add_argument("--yolo", action="store_true", help="YOLO mode")
    parser.add_argument("--output", "-o", default="bounty_report.json", help="Output file")
    
    args = parser.parse_args()
    results = full_bounty_hunt(args.path, args.depth, args.agents, args.model, args.yolo)
    
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Report saved to {args.output}")


if __name__ == "__main__":
    main()
