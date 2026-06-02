"""Hermes Swarm Loop — Unified CLI.

Provides click commands for managing phases, points, YOLO zones,
mastery gate evaluation, and workspace operations.  Designed to be
installed as a console_scripts entry point or run via ``python -m``.

Requires: click, rich, pyyaml (see pyproject.toml).
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

import click
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# ---------------------------------------------------------------------------
# Resolve project root.  When installed as a package ``engine.cli`` is
# resolved relative to the package; for development we also try the CWD.
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent

try:
    # When installed as a package, imports resolve normally
    from engine import state_machine, mastery_gate, gate_11, workspace_manager, synthesizer, config as cfg_mod
except ImportError:
    # Allow running from source without installing the package
    sys.path.insert(0, str(_PROJECT_ROOT))

from engine.state_machine import (
    ConflictError,
    PhaseMachine,
    PointMachine,
    StateDB,
    YOLOMachine,
    YOLO_ZONES,
    PhaseEntry,
    PointEntry,
    YOLOState,
)
from engine.mastery_gate import MasteryGate, ScoreCard, score_from_dict, DIMENSIONS
from engine.gate_11 import Gate11Verifier
from engine.workspace_manager import WorkspaceManager, WorkspaceKind
from engine.synthesizer import synthesize, write_artifact
from engine.config import load_config

# ---------------------------------------------------------------------------
# Console output helpers
# ---------------------------------------------------------------------------

console = Console()


def _resolve_db(project_dir: str | None) -> StateDB:
    """Resolve the swarm state DB path and return a StateDB instance."""
    cfg = _load_project_config(project_dir)
    db_rel = cfg.get("database", {}).get("path", ".swarm_state.db")
    base = Path(project_dir).resolve() if project_dir else Path.cwd().resolve()
    db_path = base / db_rel if not Path(db_rel).is_absolute() else Path(db_rel)
    return StateDB(str(db_path))


def _load_project_config(project_dir: str | None) -> dict[str, Any]:
    """Load the merged project config from *project_dir* or CWD.

    Tries: .yaml → .yml → .json
    """
    base = Path(project_dir).resolve() if project_dir else Path.cwd().resolve()
    extensions = [".yaml", ".yml", ".json"]
    for ext in extensions:
        config_paths = [
            base / "configs" / f"config{ext}",
            base / f"config{ext}",
            base / "config" / f"config{ext}",
        ]
        for p in config_paths:
            if p.is_file():
                with open(p) as f:
                    if ext in (".yaml", ".yml"):
                        return dict(yaml.safe_load(f) or {})
                    else:
                        return dict(json.load(f) or {})
    # Return empty dict — caller defaults apply
    return {}


def _print_table(title: str, columns: list[str], rows: list[list[str]]):
    """Render a rich table."""
    table = Table(title=title, title_style="bold cyan")
    for col in columns:
        table.add_column(col, style="bold")
    for row in rows:
        table.add_row(*row)
    console.print(table)


def _print_panel(text: str, title: str = "", style: str = "green"):
    """Render a rich panel."""
    console.print(Panel(text, title=title, border_style=style))


# ===========================================================================
# CLI group
# ===========================================================================


@click.group()
@click.option("--project-dir", "-d", default=None, help="Project root directory (default: CWD)")
@click.pass_context
def cli(ctx: click.Context, project_dir: str | None) -> None:
    """Hermes Swarm Loop — 3×3×11 autonomous build framework.

    Manage phases, points, YOLO zones, mastery gates, and workspaces
    for the multi-agent orchestration framework.
    """
    ctx.ensure_object(dict)
    ctx.obj["project_dir"] = project_dir or os.getcwd()


# ===========================================================================
# Phase commands
# ===========================================================================


@cli.group()
def phase() -> None:
    """Manage phases (prd_build, development, quality, hunting, simplicity)."""


@phase.command(name="start")
@click.argument("phase_name")
@click.pass_context
def phase_start(ctx: click.Context, phase_name: str) -> None:
    """Start a phase by name."""
    db = _resolve_db(ctx.obj["project_dir"])
    pm = PhaseMachine(db)
    try:
        entry = pm.start_phase(phase_name)
        _print_panel(
            f"Phase [bold]{entry.phase}[/bold] started — status: {entry.status}",
            title="Phase Started",
        )
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)


@phase.command(name="complete")
@click.argument("phase_name")
@click.pass_context
def phase_complete(ctx: click.Context, phase_name: str) -> None:
    """Complete a running phase."""
    db = _resolve_db(ctx.obj["project_dir"])
    pm = PhaseMachine(db)
    try:
        entry = pm.complete_phase(phase_name)
        _print_panel(
            f"Phase [bold]{entry.phase}[/bold] completed at {entry.completed_at}",
            title="Phase Completed",
        )
    except ConflictError as exc:
        console.print(f"[red]Conflict:[/red] {exc}")
        sys.exit(1)
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)


@phase.command(name="list")
@click.pass_context
def phase_list(ctx: click.Context) -> None:
    """List all phases and their current status."""
    db = _resolve_db(ctx.obj["project_dir"])
    pm = PhaseMachine(db)
    entries = pm.all_phases()
    if not entries:
        _print_panel("No phases found. Start one with [bold]phase start[/bold].", style="yellow")
        return
    rows = [[e.phase, e.status, e.started_at or "-", e.completed_at or "-"] for e in entries]
    _print_table("Phases", ["Phase", "Status", "Started", "Completed"], rows)


@phase.command(name="show")
@click.argument("phase_name")
@click.pass_context
def phase_show(ctx: click.Context, phase_name: str) -> None:
    """Show details for a single phase."""
    db = _resolve_db(ctx.obj["project_dir"])
    pm = PhaseMachine(db)
    entry = pm.get_phase(phase_name)
    if entry is None:
        console.print(f"[yellow]Phase '{phase_name}' not found.[/yellow]")
        return
    _print_panel(
        f"Phase:    {entry.phase}\n"
        f"Status:   {entry.status}\n"
        f"Started:  {entry.started_at or '-'}\n"
        f"Complete: {entry.completed_at or '-'}\n"
        f"Points:   {entry.completed_points}/{entry.total_points}",
        title=f"Phase: {phase_name}",
    )


# ===========================================================================
# Point commands
# ===========================================================================


@cli.group()
def point() -> None:
    """Manage points within phases."""


@point.command(name="create")
@click.argument("phase_name")
@click.argument("point_name")
@click.option("--agents", "-a", default=11, type=int, help="Agent count (default: 11)")
@click.pass_context
def point_create(ctx: click.Context, phase_name: str, point_name: str, agents: int) -> None:
    """Create a point within a phase."""
    db = _resolve_db(ctx.obj["project_dir"])
    ptm = PointMachine(db)
    try:
        entry = ptm.create_point(phase_name, point_name, agent_count=agents)
        _print_panel(
            f"Point [bold]{entry.point}[/bold] created in phase '{entry.phase}' "
            f"with {entry.agent_count} agents — status: {entry.status}",
            title="Point Created",
        )
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)


@point.command(name="complete")
@click.argument("phase_name")
@click.argument("point_name")
@click.pass_context
def point_complete(ctx: click.Context, phase_name: str, point_name: str) -> None:
    """Mark a point as complete."""
    db = _resolve_db(ctx.obj["project_dir"])
    ptm = PointMachine(db)
    try:
        entry = ptm.complete_point(phase_name, point_name)
        _print_panel(
            f"Point [bold]{entry.point}[/bold] completed at {entry.completed_at}",
            title="Point Completed",
        )
    except ConflictError as exc:
        console.print(f"[red]Conflict:[/red] {exc}")
        sys.exit(1)


@point.command(name="list")
@click.option("--phase", "-p", default=None, help="Filter by phase name")
@click.pass_context
def point_list(ctx: click.Context, phase: str | None) -> None:
    """List points, optionally filtered by phase."""
    db = _resolve_db(ctx.obj["project_dir"])
    ptm = PointMachine(db)
    if phase:
        entries = ptm.get_points_for_phase(phase)
    else:
        entries = ptm.all_points()
    if not entries:
        _print_panel("No points found.", style="yellow")
        return
    rows = [
        [e.phase, e.point, e.status, str(e.agent_count), e.started_at or "-", e.completed_at or "-"]
        for e in entries
    ]
    _print_table("Points", ["Phase", "Point", "Status", "Agents", "Started", "Completed"], rows)


@point.command(name="show")
@click.argument("phase_name")
@click.argument("point_name")
@click.pass_context
def point_show(ctx: click.Context, phase_name: str, point_name: str) -> None:
    """Show details for a single point."""
    db = _resolve_db(ctx.obj["project_dir"])
    ptm = PointMachine(db)
    entry = ptm.get_point(phase_name, point_name)
    if entry is None:
        console.print(f"[yellow]Point '{phase_name}/{point_name}' not found.[/yellow]")
        return
    _print_panel(
        f"Phase:    {entry.phase}\n"
        f"Point:    {entry.point}\n"
        f"Status:   {entry.status}\n"
        f"Agents:   {entry.agent_count}\n"
        f"Started:  {entry.started_at or '-'}\n"
        f"Complete: {entry.completed_at or '-'}",
        title=f"Point: {phase_name}/{point_name}",
    )


# ===========================================================================
# YOLO commands
# ===========================================================================


@cli.group()
def yolo() -> None:
    """Manage YOLO zones (safe, test, staging, production)."""


@yolo.command(name="set")
@click.argument("zone_name")
@click.pass_context
def yolo_set(ctx: click.Context, zone_name: str) -> None:
    """Set the active YOLO zone."""
    db = _resolve_db(ctx.obj["project_dir"])
    ym = YOLOMachine(db)
    try:
        state = ym.set_zone(zone_name)
        _print_panel(
            f"Zone:        {state.zone}\n"
            f"Auto-approve: {state.auto_approve}\n"
            f"Max parallel: {state.max_parallel}\n"
            f"Safety valve: {state.safety_valve_active}",
            title=f"YOLO Zone: {zone_name}",
        )
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)


@yolo.command(name="status")
@click.pass_context
def yolo_status(ctx: click.Context) -> None:
    """Show the current YOLO zone state."""
    db = _resolve_db(ctx.obj["project_dir"])
    ym = YOLOMachine(db)
    state = ym.get_state()
    _print_panel(
        f"Zone:            {state.zone}\n"
        f"Auto-approve:    {state.auto_approve}\n"
        f"Max parallel:    {state.max_parallel}\n"
        f"Safety valve:    {state.safety_valve_active}\n"
        f"Consec. errors:  {state.consecutive_errors}",
        title="YOLO Status",
    )


@yolo.command(name="list")
def yolo_list() -> None:
    """List all available YOLO zones."""
    rows = [
        [z, str(cfg["auto_approve"]), str(cfg["max_parallel"]), cfg["desc"]]
        for z, cfg in YOLO_ZONES.items()
    ]
    _print_table("YOLO Zones", ["Zone", "Auto-Approve", "Max Parallel", "Description"], rows)


@yolo.command(name="error")
@click.pass_context
def yolo_error(ctx: click.Context) -> None:
    """Increment the consecutive error counter (triggers safety valve at 5)."""
    db = _resolve_db(ctx.obj["project_dir"])
    ym = YOLOMachine(db)
    state = ym.increment_errors()
    _print_panel(
        f"Consecutive errors: {state.consecutive_errors}\n"
        f"Safety valve: {(state.safety_valve_active)}\n"
        f"Zone: {state.zone}  Parallel: {state.max_parallel}",
        title="YOLO Error Incremented",
    )


@yolo.command(name="reset")
@click.pass_context
def yolo_reset(ctx: click.Context) -> None:
    """Reset the safety valve and error counter."""
    db = _resolve_db(ctx.obj["project_dir"])
    ym = YOLOMachine(db)
    state = ym.reset_safety_valve()
    _print_panel(
        f"Safety valve reset. Current errors: {state.consecutive_errors}",
        title="YOLO Reset",
    )


@yolo.command(name="activate-valve")
@click.pass_context
def yolo_activate_valve(ctx: click.Context) -> None:
    """Manually activate the safety valve."""
    db = _resolve_db(ctx.obj["project_dir"])
    ym = YOLOMachine(db)
    state = ym.activate_safety_valve()
    _print_panel(f"Safety valve active. Max parallel reduced to {state.max_parallel}.", style="red")


# ===========================================================================
# Mastery Gate commands
# ===========================================================================


@cli.group()
def gate() -> None:
    """Evaluate mastery gates across phases/points."""


@gate.command(name="evaluate")
@click.option("--scores", "-s", type=str, default=None,
              help="JSON string or file path of agent scores array")
@click.option("--phase", "-p", default="development", help="Phase name")
@click.option("--point", "-pt", default="code_generation", help="Point name")
@click.pass_context
def gate_evaluate(
    ctx: click.Context,
    scores: str | None,
    phase: str,
    point: str,
) -> None:
    """Evaluate a mastery gate from agent scores.

    Scores should be a JSON array of ScoreCard-like objects with
    dimension keys: correctness, safety, test_coverage, consistency,
    diversity, efficiency, clarity.
    """
    if scores is None:
        # Prompt for interactive input
        console.print("[yellow]No scores provided. Using sample scores.[/yellow]")
        agent_scores = [
            ScoreCard(correctness=0.85, safety=0.80, test_coverage=0.75,
                      consistency=0.80, diversity=0.70, efficiency=0.85, clarity=0.90),
            ScoreCard(correctness=0.80, safety=0.85, test_coverage=0.70,
                      consistency=0.75, diversity=0.75, efficiency=0.80, clarity=0.85),
        ]
    else:
        # Parse scores — either a file path or inline JSON
        score_path = Path(scores)
        if score_path.is_file():
            raw = score_path.read_text()
        else:
            raw = scores
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            console.print(f"[red]Invalid JSON:[/red] {exc}")
            sys.exit(1)
        if isinstance(data, dict):
            data = [data]
        agent_scores = [score_from_dict(d) for d in data]

    mg = MasteryGate()
    result = mg.evaluate(agent_scores)
    out = mg.as_dict(phase, point, result, agents_used=len(agent_scores))

    # Print results
    verdict_style = {
        "PASS": "green",
        "CROSS-CHECK": "yellow",
        "REVIEW": "red",
        "BLOCK": "red bold",
    }.get(out["score"]["verdict"], "white")

    score_lines = [f"[bold]{dim}:[/bold] {out['score']['scores'][dim]:.4f}" for dim in DIMENSIONS]
    score_lines.append(f"\n[bold]Weighted total:[/bold] {out['score']['weighted_total']:.4f}")
    score_lines.append(f"[bold]{'Verdict':>17}:[/bold] [{verdict_style}]{out['score']['verdict']}[/{verdict_style}]")
    score_lines.append(f"[bold]Agents:[/bold] {out['agents_used']}")
    score_lines.append(f"[bold]Time:[/bold] {out['time_seconds']:.2f}s")
    if out["gaps"]:
        score_lines.append(f"\n[bold yellow]Gaps:[/bold yellow]")
        for g in out["gaps"]:
            score_lines.append(f"  • {g}")
    else:
        score_lines.append(f"\n[green]No gaps detected.[/green]")

    _print_panel("\n".join(score_lines), title=f"Mastery Gate: {phase}/{point}", style=verdict_style)


@gate.command(name="dimensions")
def gate_dimensions() -> None:
    """Show mastery gate dimensions and weights."""
    rows = [[dim, f"{w:.2f}"] for dim, w in sorted(DIMENSIONS.items(), key=lambda x: -x[1])]
    rows.append(["[bold]Total[/bold]", "[bold]1.00[/bold]"])
    _print_table("Mastery Gate Dimensions", ["Dimension", "Weight"], rows)
    _print_panel(
        "Thresholds:\n"
        "  PASS        ≥ 0.70\n"
        "  CROSS-CHECK  0.50 – 0.69\n"
        "  REVIEW       0.30 – 0.49\n"
        "  BLOCK        < 0.30",
        title="Thresholds",
    )


# ===========================================================================
# Workspace commands
# ===========================================================================


@cli.group()
def workspace() -> None:
    """Manage scratch/dir/worktree workspaces."""


@workspace.command(name="create")
@click.argument("kind", type=click.Choice(["scratch", "dir", "worktree"]))
@click.option("--task-id", "-t", default="", help="Task identifier for workspace naming")
@click.option("--dir-path", default=None, help="Absolute path for 'dir' workspace")
@click.option("--label", "-l", default="", help="Human-friendly label")
@click.option("--repo", "-r", default=None, help="Main repo path for worktree")
@click.pass_context
def workspace_create(
    ctx: click.Context,
    kind: str,
    task_id: str,
    dir_path: str | None,
    label: str,
    repo: str | None,
) -> None:
    """Create a workspace of the given kind."""
    wm = WorkspaceManager(main_repo=repo)
    try:
        ws = wm.setup(kind, task_id=task_id, dir_path=dir_path, label=label)
        _print_panel(
            f"Kind:    {ws.kind.value}\n"
            f"Path:    {ws.path}\n"
            f"Label:   {ws.label or '-'}\n"
            f"Ready:   {(ws.is_ready)}",
            title="Workspace Created",
        )
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)


@workspace.command(name="list")
@click.pass_context
def workspace_list(ctx: click.Context) -> None:
    """List active workspaces."""
    wm = WorkspaceManager()
    active = wm.list_active()
    if not active:
        _print_panel("No active workspaces.", style="yellow")
        return
    rows = [
        [ws.kind.value, str(ws.path), ws.label or "-",
         "yes" if ws.is_ready else "no"]
        for ws in active
    ]
    _print_table("Active Workspaces", ["Kind", "Path", "Label", "Ready"], rows)


# ===========================================================================
# Swarm commands
# ===========================================================================


@cli.group()
def swarm() -> None:
    """High-level swarm orchestration commands."""


@swarm.command(name="status")
@click.pass_context
def swarm_status(ctx: click.Context) -> None:
    """Show a comprehensive status overview of the entire swarm."""
    db = _resolve_db(ctx.obj["project_dir"])
    pm = PhaseMachine(db)
    ptm = PointMachine(db)
    ym = YOLOMachine(db)

    # Phase summary
    phases = pm.all_phases()
    if phases:
        phase_rows = [[e.phase, e.status, str(e.completed_points) + "/" + str(e.total_points)] for e in phases]
        _print_table("Phases", ["Phase", "Status", "Points Done"], phase_rows)
    else:
        _print_panel("No phases started yet.", style="yellow")

    # Point summary
    points = ptm.all_points()
    if points:
        point_rows = [
            [e.phase, e.point, e.status, str(e.agent_count)]
            for e in points[:20]  # cap display
        ]
        _print_table("Recent Points", ["Phase", "Point", "Status", "Agents"], point_rows)

    # YOLO state
    state = ym.get_state()
    _print_panel(
        f"Zone: {state.zone}  |  Parallel: {state.max_parallel}  |  "
        f"Auto: {state.auto_approve}  |  Safety: {state.safety_valve_active}  |  "
        f"Errors: {state.consecutive_errors}",
        title="YOLO",
    )


# ===========================================================================
# Config commands
# ===========================================================================


@cli.group()
def config() -> None:
    """Inspect project configuration."""


@config.command(name="show")
@click.option("--key", "-k", default=None, help="Show a specific config key (dot-separated)")
@click.pass_context
def config_show(ctx: click.Context, key: str | None) -> None:
    """Show the merged project configuration."""
    cfg = _load_project_config(ctx.obj["project_dir"])
    if not cfg:
        _print_panel("No configuration file found.", style="yellow")
        return

    if key:
        parts = key.split(".")
        val: Any = cfg
        for part in parts:
            if isinstance(val, dict):
                val = val.get(part)
            else:
                val = None
                break
        if val is None:
            console.print(f"[yellow]Key '{key}' not found in config.[/yellow]")
            return
        console.print(yaml.dump({key: val}, default_flow_style=False).strip())
    else:
        console.print(yaml.dump(cfg, default_flow_style=False).strip())


# ===========================================================================
# Entry point
# ===========================================================================

def main() -> None:
    """CLI entry point — called by console_scripts or __main__."""
    cli()


if __name__ == "__main__":
    main()
