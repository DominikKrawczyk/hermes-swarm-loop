#!/usr/bin/env python3
"""
Hermes Swarm Loop — Self-Reflection Engine

Analyzes iteration results and determines:
  1. Is this a MASTERPIECE? (ship it)
  2. Is it FLAWED? (loop again with deeper focus)
  3. What specific areas need more work?
  4. Can anything be further improved?

Reflection dimensions:
  - Code quality: readability, maintainability, test coverage
  - Architecture: design decisions, trade-offs, scalability
  - Security: vulnerability surface, threat model coverage
  - Completeness: does it actually solve the problem?
  - Novelty: is it innovative or just rehashing?
  - Confidence: how sure are we about the assessment?
"""

import json
import sys
from typing import Optional
from pathlib import Path


def reflect(state_path: str = "swarm_state.json") -> dict:
    """Run self-reflection on saved loop state."""
    
    with open(state_path) as f:
        state = json.load(f)
    
    print(f"\n{'★'*60}")
    print(f"🪞 SELF-REFLECTION ENGINE")
    print(f"{'★'*60}")
    print(f"  Project: {state.get('project', {}).get('name', 'unknown')}")
    print(f"  Cycles completed: {state.get('current_cycle', 0)}")
    print(f"  Total agents used: {state.get('project', {}).get('total_agents_used', 0)}")
    print(f"{'★'*60}\n")
    
    history = state.get("history", [])
    if not history:
        return {"is_masterpiece": False, "reason": "no_history"}
    
    latest = history[-1]
    
    # ─── Dimension Analysis ───
    
    dimensions = {
        "code_quality": _assess_code_quality(latest, history),
        "architecture": _assess_architecture(latest, history),
        "security": _assess_security(latest, history),
        "completeness": _assess_completeness(latest, state),
        "novelty": _assess_novelty(latest, history),
    }
    
    # ─── Trend Analysis ───
    trend = _analyze_trend(history)
    
    # ─── Final Judgment ───
    
    score = sum(d["score"] for d in dimensions.values()) / len(dimensions)
    min_score = min(d["score"] for d in dimensions.values())
    flaws = latest.get("flaws_found", 99)
    cycles = state.get("current_cycle", 0)
    
    is_masterpiece = (
        score >= 0.85 and      # Overall quality threshold
        min_score >= 0.7 and    # No weak dimensions
        flaws < 5 and           # Minimal remaining flaws
        cycles >= 3 and         # At least 3 cycles (meaningful iteration)
        trend == "improving"    # Still getting better? No → masterpiece
    )
    
    verdict = {
        "is_masterpiece": is_masterpiece,
        "confidence": round(score, 3),
        "overall_score": round(score, 3),
        "minimum_dimension_score": round(min_score, 3),
        "trend": trend,
        "flaws_remaining": flaws,
        "cycles_completed": cycles,
        "dimensions": {k: v["label"] for k, v in dimensions.items()},
        "dimension_scores": {k: round(v["score"], 3) for k, v in dimensions.items()},
        "weakest_link": min(dimensions, key=lambda k: dimensions[k]["score"]),
        "recommendation": _recommendation(score, min_score, flaws, cycles, trend),
        "can_be_further_improved": flaws > 0 and not is_masterpiece,
    }
    
    # ─── Print Report ───
    
    print(f"  {'='*50}")
    print(f"  DIMENSION SCORES")
    print(f"  {'='*50}")
    for dim, data in dimensions.items():
        bar = "█" * int(data["score"] * 20) + "░" * (20 - int(data["score"] * 20))
        print(f"  {dim:20s} [{bar}] {data['score']:.0%}  — {data['label']}")
    
    print(f"")
    print(f"  {'='*50}")
    print(f"  TREND: {trend.upper()}")
    print(f"  FLAWS REMAINING: {flaws}")
    print(f"  CYCLES: {cycles}")
    print(f"  {'='*50}")
    print(f"")
    
    if is_masterpiece:
        print(f"  ✅ MASTERPIECE VERDICT — SHIP IT!")
    else:
        weakest = verdict["weakest_link"]
        print(f"  🔄 NOT YET — weakest: {weakest} ({dimensions[weakest]['score']:.0%})")
        print(f"  💡 Focus next cycle on: {weakest}")
    
    print(f"  {verdict['recommendation']}")
    print(f"")
    
    return verdict


def _assess_code_quality(latest: dict, history: list) -> dict:
    """Assess code quality from iteration results."""
    audit = latest.get("audit", {})
    improve = latest.get("improve", {})
    
    findings_count = len(audit.get("findings", []))
    changes_count = len(improve.get("changes", []))
    
    # More findings + more changes = more code churn = lower quality
    # Fewer findings + meaningful changes = higher quality
    score = 1.0 - min(0.5, findings_count * 0.02 + changes_count * 0.01)
    
    label = "excellent" if score > 0.85 else "good" if score > 0.7 else "needs work" if score > 0.5 else "poor"
    return {"score": score, "label": label, "findings": findings_count, "changes": changes_count}


def _assess_architecture(latest: dict, history: list) -> dict:
    """Assess architectural quality."""
    review = latest.get("review", {})
    feedback = review.get("feedback", [])
    
    arch_issues = [f for f in feedback if isinstance(f, dict) and f.get("type") == "architecture"]
    
    score = 1.0 - min(0.5, len(arch_issues) * 0.1)
    label = "solid" if score > 0.85 else "decent" if score > 0.7 else "needs refactoring"
    return {"score": score, "label": label, "issues": len(arch_issues)}


def _assess_security(latest: dict, history: list) -> dict:
    """Assess security posture."""
    review = latest.get("review", {})
    feedback = review.get("feedback", [])
    
    sec_issues = [f for f in feedback if isinstance(f, dict) and f.get("type") == "security"]
    critical = [f for f in sec_issues if isinstance(f, dict) and f.get("severity") == "CRITICAL"]
    
    # Even one critical = fail
    if critical:
        score = 0.3
    else:
        score = 1.0 - min(0.5, len(sec_issues) * 0.12)
    
    label = "secure" if score > 0.85 else "acceptable" if score > 0.7 else "needs hardening"
    return {"score": score, "label": label, "critical": len(critical), "issues": len(sec_issues)}


def _assess_completeness(latest: dict, state: dict) -> dict:
    """Assess how complete the project is."""
    project = state.get("project", {})
    features = project.get("implemented_features", [])
    
    cycles = state.get("current_cycle", 0)
    
    # More cycles = more complete
    score = min(1.0, cycles * 0.15 + 0.3)
    
    label = "complete" if score > 0.85 else "mostly done" if score > 0.7 else "in progress"
    return {"score": score, "label": label, "features": len(features), "cycles": cycles}


def _assess_novelty(latest: dict, history: list) -> dict:
    """Assess novelty/innovation."""
    # Novelty is harder to measure programmatically
    # Default to reasonable score, decreases with many iterations
    cycles = len(history)
    score = max(0.6, 0.9 - cycles * 0.02)  # Diminishing novelty per cycle
    label = "innovative" if score > 0.8 else "solid" if score > 0.6 else "iterative"
    return {"score": score, "label": label}


def _analyze_trend(history: list) -> str:
    """Analyze quality trend across iterations."""
    if len(history) < 2:
        return "stable"
    
    recent = history[-3:] if len(history) >= 3 else history
    
    # Check if flaws are decreasing
    flaw_counts = [h.get("flaws_found", 99) for h in recent]
    if len(flaw_counts) >= 2:
        if flaw_counts[-1] < flaw_counts[0]:
            return "improving"
        elif flaw_counts[-1] > flaw_counts[0]:
            return "degrading"
    
    return "stable"


def _recommendation(score: float, min_score: float, flaws: int, 
                    cycles: int, trend: str) -> str:
    """Generate human-readable recommendation."""
    if score >= 0.9 and flaws == 0 and cycles >= 3:
        return "✅ SHIP IT — This is ready. Push to production."
    elif score >= 0.85 and flaws < 3:
        return "✅ NEARLY THERE — One more polish cycle recommended."
    elif trend == "degrading":
        return "⚠️ RE-EVALUATE APPROACH — Quality is degrading. Consider architectural changes."
    elif min_score < 0.5:
        weakest = "the weakest dimension"
        return f"🔄 FOCUS NEEDED — {weakest} requires significant improvement before proceeding."
    else:
        return "🔄 CONTINUING — Standard iteration cycle. Keep improving."


if __name__ == "__main__":
    state_file = sys.argv[1] if len(sys.argv) > 1 else "swarm_state.json"
    if not Path(state_file).exists():
        print(f"❌ State file not found: {state_file}")
        print(f"   Usage: {sys.argv[0]} [state_file.json]")
        sys.exit(1)
    
    result = reflect(state_file)
    
    with open("reflection_result.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\n💾 Reflection saved to reflection_result.json")
