"""
Gate 11 Verifier — Hermes Swarm Loop
======================================
Verifies that all 11 agents in a point completed before the point
advances. Validates JSON-schema handoffs from workers.

Called by the verifier profile between worker-complete and
synthesizer-run stages of kanban swarm.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional


MINIMUM_HANDOFF_FIELDS = {
    "summary": str,
    "worker_id": str,
    "point": str,
    "phase": str,
}


@dataclass
class HandoffValidation:
    """Result of validating a single agent's handoff."""

    worker_id: str
    valid: bool
    errors: list[str] = field(default_factory=list)
    handoff: dict = field(default_factory=dict)


@dataclass
class GateResult:
    """Aggregate result of verifying the full 11-agent gate."""

    passed: bool
    total_agents: int
    completed_agents: int
    validations: list[HandoffValidation] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    all_done: bool = False

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "total_agents": self.total_agents,
            "completed_agents": self.completed_agents,
            "errors": self.errors,
            "all_done": self.all_done,
        }


class Gate11Verifier:
    """Verifies that the 11-agent gate has passed for a point."""

    REQUIRED_COUNT = 11

    def validate_handoff(self, handoff: dict, worker_id: str) -> HandoffValidation:
        """Validate a single worker's handoff against the minimum schema."""
        errors = []
        for field_name, field_type in MINIMUM_HANDOFF_FIELDS.items():
            if field_name not in handoff:
                errors.append(f"missing field: {field_name}")
            elif not isinstance(handoff[field_name], field_type):
                errors.append(
                    f"field '{field_name}' wrong type: "
                    f"expected {field_type.__name__}, got {type(handoff[field_name]).__name__}"
                )
        return HandoffValidation(
            worker_id=worker_id,
            valid=len(errors) == 0,
            errors=errors,
            handoff=handoff,
        )

    def verify(self, handoffs: list[dict]) -> GateResult:
        """Verify that all 11 agents completed with valid handoffs."""
        result = GateResult(
            passed=False,
            total_agents=self.REQUIRED_COUNT,
            completed_agents=len(handoffs),
        )

        if len(handoffs) < self.REQUIRED_COUNT:
            result.errors.append(
                f"Not enough agents completed: {len(handoffs)}/{self.REQUIRED_COUNT}"
            )
            return result

        for h in handoffs:
            wid = h.get("worker_id", "unknown")
            v = self.validate_handoff(h, wid)
            result.validations.append(v)
            if not v.valid:
                result.errors.append(f"Worker {wid}: {'; '.join(v.errors)}")

        completed = sum(1 for h in handoffs if h.get("status") == "done")
        result.completed_agents = completed
        result.all_done = completed >= self.REQUIRED_COUNT
        result.passed = result.all_done and len(result.errors) == 0
        return result

    def verify_from_json(self, raw: str) -> GateResult:
        """Parse JSON string of handoff list and verify."""
        try:
            handoffs = json.loads(raw)
        except json.JSONDecodeError as exc:
            return GateResult(
                passed=False,
                total_agents=self.REQUIRED_COUNT,
                completed_agents=0,
                errors=[f"Invalid JSON: {exc}"],
            )
        if not isinstance(handoffs, list):
            return GateResult(
                passed=False,
                total_agents=self.REQUIRED_COUNT,
                completed_agents=0,
                errors=[f"Expected JSON array of handoffs, got {type(handoffs).__name__}"],
            )
        return self.verify(handoffs)
