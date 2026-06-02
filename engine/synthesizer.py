"""Output synthesizer — merges parallel agent outputs into coherent artifacts."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def synthesize(
    agent_outputs: list[dict[str, Any]],
    synthesis_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge parallel agent outputs into a single synthesized artifact.

    Args:
        agent_outputs: List of agent result dicts, each with at least:
            - agent_id: str
            - output: dict (structured findings)
            - status: str ('completed', 'failed', 'skipped')
        synthesis_plan: Optional plan dict with merge strategy

    Returns:
        Synthesized output with:
            - merged_findings: deduplicated combined findings
            - agent_count: total agents
            - completed_count: how many finished
            - synthesis_timestamp: ISO timestamp
    """
    completed = [o for o in agent_outputs if o.get("status") == "completed"]
    failed = [o for o in agent_outputs if o.get("status") == "failed"]

    if synthesis_plan is None:
        synthesis_plan = {"merge_strategy": "dedup_append", "output_format": "json"}

    # Merge all outputs
    all_findings: list[dict[str, Any]] = []
    seen_keys: set = set()

    for agent_out in completed:
        output = agent_out.get("output", {})
        findings = output if isinstance(output, list) else output.get("findings", [])

        for finding in findings if isinstance(findings, list) else [findings]:
            # Dedup by content hash
            key = _finding_key(finding)
            if key not in seen_keys:
                seen_keys.add(key)
                all_findings.append(finding)

    # Defensive dedup_count: handle non-list output types (e.g. str, dict)
    total_output_items = 0
    for o in completed:
        raw = o.get("output")
        if isinstance(raw, list):
            total_output_items += len(raw)
        elif isinstance(raw, dict):
            inner = raw.get("findings", [])
            total_output_items += len(inner) if isinstance(inner, list) else 1
        elif raw is not None:
            total_output_items += 1

    merged = {
        "merged_findings": all_findings,
        "agent_count": len(agent_outputs),
        "completed_count": len(completed),
        "failed_count": len(failed),
        "synthesis_timestamp": datetime.now(timezone.utc).isoformat(),
        "synthesis_plan": synthesis_plan,
        "dedup_count": total_output_items - len(all_findings)
        if completed
        else 0,
    }

    return merged


def write_artifact(output: dict[str, Any], path: str) -> str:
    """Write synthesized output to a JSON artifact file.

    Args:
        output: The merged artifact dict
        path: Destination path (relative to project root or absolute)

    Returns:
        Absolute path to the written file
    """
    dst = Path(path)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(output, indent=2, default=str))
    return str(dst.resolve())


def _finding_key(finding: Any) -> str:
    """Generate a dedup key for a finding."""
    if isinstance(finding, dict):
        # Use a hash of the serialized content for dedup
        return json.dumps(finding, sort_keys=True, default=str)
    return str(finding)
