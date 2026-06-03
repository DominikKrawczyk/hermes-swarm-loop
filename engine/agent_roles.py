"""Agent role definitions for Hermes Swarm Loop — 198 roles across all phases."""
from __future__ import annotations

from typing import Any

DOMAINS = [
    "state_machine", "mastery_gate", "scaling", "workspace_management",
    "yolo_zones", "agent_roles", "bootstrap", "testing", "ci_cd",
    "logging", "config_management", "error_handling", "concurrency",
    "data_model", "api_design", "cli", "documentation", "security",
    "performance", "observability", "recovery", "orchestration",
    "communication", "storage", "network", "deployment", "monitoring",
    "quality_gates", "feedback_loops", "self_reflection", "versioning",
    "migration", "compatibility",
]


def _domain_for(index: int) -> str:
    """Map a 1-indexed agent number to a domain name from DOMAINS.

    Args:
        index: 1-indexed agent number. Callers **must** pass
            values starting at 1 (e.g. ``range(1, N+1)``).
            Passing 0-based indices will silently shift the
            distribution off by one.

    Returns:
        The domain name at ``DOMAINS[(index - 1) % len(DOMAINS)]``.
    """
    return DOMAINS[(index - 1) % len(DOMAINS)]

AGENT_ROLES: dict[str, list[dict[str, Any]]] = {
    "prd_build": [
        {"name": f"prd_researcher_{i:02d}", "kind": "research",
         "domain": _domain_for(i), "description": f"Research agent {i} — {_domain_for(i)}"}
        for i in range(1, 23)
    ] + [
        {"name": f"prd_question_{i:02d}", "kind": "questions",
         "domain": _domain_for(i), "description": f"Questions agent {i} — {_domain_for(i)}"}
        for i in range(1, 23)
    ] + [
        {"name": f"prd_builder_{i:02d}", "kind": "build",
         "domain": _domain_for(i), "description": f"Build agent {i} — {_domain_for(i)}"}
        for i in range(1, 23)
    ],
    "development": [
        {"name": f"architect_{i:02d}", "kind": "architecture",
         "domain": _domain_for(i), "description": f"Architecture design agent {i}"}
        for i in range(1, 12)
    ] + [
        {"name": f"setup_{i:02d}", "kind": "setup",
         "domain": _domain_for(i), "description": f"Project setup agent {i}"}
        for i in range(1, 12)
    ] + [
        {"name": f"code_gen_{i:02d}", "kind": "code_generation",
         "domain": _domain_for(i), "description": f"Code generation agent {i}"}
        for i in range(1, 12)
    ],
    "quality": [
        {"name": f"auditor_{i:02d}", "kind": "audit",
         "domain": _domain_for(i), "description": f"Code auditor agent {i}"}
        for i in range(1, 12)
    ] + [
        {"name": f"improver_{i:02d}", "kind": "improve",
         "domain": _domain_for(i), "description": f"Improvement agent {i}"}
        for i in range(1, 12)
    ] + [
        {"name": f"reviewer_{i:02d}", "kind": "review",
         "domain": _domain_for(i), "description": f"Reviewer agent {i}"}
        for i in range(1, 12)
    ],
    "hunting": [
        {"name": f"bug_hunter_{i:02d}", "kind": "bugs",
         "domain": _domain_for(i), "description": f"Bug hunting agent {i}"}
        for i in range(1, 12)
    ] + [
        {"name": f"arch_reviewer_{i:02d}", "kind": "arch_review",
         "domain": _domain_for(i), "description": f"Architecture review agent {i}"}
        for i in range(1, 12)
    ] + [
        {"name": f"security_{i:02d}", "kind": "security",
         "domain": _domain_for(i), "description": f"Security audit agent {i}"}
        for i in range(1, 12)
    ],
    "simplicity": [
        {"name": f"dead_code_{i:02d}", "kind": "dead_code",
         "domain": _domain_for(i), "description": f"Dead code consolidation agent {i}"}
        for i in range(1, 12)
    ] + [
        {"name": f"occam_{i:02d}", "kind": "occam",
         "domain": _domain_for(i), "description": f"Occam's razor agent {i}"}
        for i in range(1, 12)
    ] + [
        {"name": f"prd_align_{i:02d}", "kind": "prd_alignment",
         "domain": _domain_for(i), "description": f"PRD alignment agent {i}"}
        for i in range(1, 12)
    ],
}

def total_roles() -> int:
    """Return total number of defined agent roles."""
    return sum(len(roles) for roles in AGENT_ROLES.values())


def get_roles_for_phase(phase: str) -> list:
    """Return all agent roles for a given phase."""
    return AGENT_ROLES.get(phase, [])


def get_role(name: str) -> dict | None:
    """Find a specific role by name across all phases."""
    for phase_roles in AGENT_ROLES.values():
        for role in phase_roles:
            if role["name"] == name:
                return role
    return None
