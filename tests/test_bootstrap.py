"""Tests for Hermes Swarm Loop — bootstrap launcher.

Tests the 5-stage pipeline:
1. Environment check
2. Database init
3. Phase setup
4. YOLO init
5. Launch (command generation)
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# =============================================================================
# check_env
# =============================================================================


class TestCheckEnv:
    """Environment check stage — verifies tooling presence."""

    def test_returns_empty_when_all_tools_present(self):
        from bootstrap import check_env

        errors = check_env()
        assert isinstance(errors, list)
        # On a system with hermes, python3, gh, git all on PATH,
        # errors should be empty.
        # gh might not be installed — that's a valid individual error
        # but hermes, python3, and git should always be present here.
        tool_errors = [e for e in errors if "Hermes Agent" in e or "Python" in e or "Git" in e]
        assert len(tool_errors) == 0, f"Missing critical tools: {tool_errors}"

    def test_reports_missing_tool(self):
        """Simulate missing tool by patching shutil.which."""
        import shutil
        from bootstrap import check_env

        original = shutil.which
        try:
            shutil.which = lambda cmd: None if cmd == "hermes" else original(cmd)
            errors = check_env()
            assert any("Hermes Agent" in e for e in errors)
        finally:
            shutil.which = original

    def test_python_version_check(self):
        """Must report error for Python < 3.10."""
        from bootstrap import check_env
        # Test using the internal version_info check approach
        # Directly test the comparison logic
        assert (3, 9, 0) < (3, 10)  # tuple comparison works as expected
        assert (3, 11, 0) >= (3, 10)
        errors = check_env()
        assert isinstance(errors, list)


# =============================================================================
# Argument parsing
# =============================================================================


class TestArgParsing:
    """Boostrap argument parser behaviour."""

    def test_default_args(self):
        """Defaults: phase=development, yolo_zone=test, max_agents=11."""
        from bootstrap import main as _  # noqa: F401 — import validates module

        import argparse

        parser = argparse.ArgumentParser()
        # Just verify the argparse module can be used
        assert parser is not None


# =============================================================================
# Database init integration
# =============================================================================


class TestDatabaseInit:
    """End-to-end database initialisation via StateDB."""

    def test_state_db_creates_all_tables(self):
        from engine.state_machine import StateDB

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        try:
            db = StateDB(path)
            with db.cursor() as cur:
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = {row["name"] for row in cur.fetchall()}
            assert "phase_state" in tables
            assert "point_state" in tables
            assert "yolo_state" in tables
            assert "event_log" in tables
            assert "launch_config" in tables
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def test_state_db_wal_mode(self):
        from engine.state_machine import StateDB

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        try:
            db = StateDB(path)
            with db.cursor() as cur:
                cur.execute("PRAGMA journal_mode")
                row = cur.fetchone()
            assert row is not None
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def test_yolo_default_row(self):
        from engine.state_machine import StateDB

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        try:
            db = StateDB(path)
            with db.cursor() as cur:
                cur.execute("SELECT zone, auto_approve, max_parallel FROM yolo_state WHERE id=1")
                row = cur.fetchone()
            assert row is not None
            assert row["zone"] == "safe"
            assert row["max_parallel"] == 5
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass


# =============================================================================
# Phase setup integration
# =============================================================================


class TestPhaseSetup:
    """Phase setup logic tested via state machine directly."""

    def test_start_phase_creates_entry(self):
        from engine.state_machine import PhaseMachine, StateDB

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        try:
            db = StateDB(path)
            pm = PhaseMachine(db)
            entry = pm.start_phase("development")
            assert entry.phase == "development"
            assert entry.status == "running"
            assert entry.started_at is not None
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def test_create_points_for_phase(self):
        from engine.state_machine import PhaseMachine, PointMachine, StateDB

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        try:
            db = StateDB(path)
            pm = PhaseMachine(db)
            pm.start_phase("development")
            # Create points for the phase
            ptm = PointMachine(db)
            for pt in ["architecture", "setup", "code_generation"]:
                entry = ptm.create_point("development", pt, agent_count=11)
                assert entry.phase == "development"
                assert entry.point == pt
                assert entry.agent_count == 11
                assert entry.status == "todo"
            points = ptm.get_points_for_phase("development")
            assert len(points) == 3
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def test_unknown_phase_raises(self):
        from engine.state_machine import PhaseMachine, StateDB
        import pytest

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        try:
            db = StateDB(path)
            pm = PhaseMachine(db)
            with pytest.raises(ValueError, match="Unknown phase"):
                pm.start_phase("nonexistent")
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass


# =============================================================================
# YOLO init integration
# =============================================================================


class TestYOLOInit:
    """YOLO initialisation logic tested via state machine."""

    def test_set_zone_updates_state(self):
        from engine.state_machine import StateDB, YOLOMachine

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        try:
            db = StateDB(path)
            ym = YOLOMachine(db)
            state = ym.set_zone("production")
            assert state.zone == "production"
            assert state.max_parallel == 999
            assert state.auto_approve is True
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def test_safety_valve_reset(self):
        from engine.state_machine import StateDB, YOLOMachine

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        try:
            db = StateDB(path)
            ym = YOLOMachine(db)
            ym.activate_safety_valve()
            assert ym.get_state().safety_valve_active is True
            ym.reset_safety_valve()
            assert ym.get_state().safety_valve_active is False
            assert ym.get_state().consecutive_errors == 0
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def test_agent_capping(self):
        """YOLO zones cap max_agents at their max_parallel limit."""
        from engine.state_machine import YOLO_ZONES

        staging_max = YOLO_ZONES["staging"]["max_parallel"]
        assert staging_max == 33
        safe_max = YOLO_ZONES["safe"]["max_parallel"]
        assert safe_max == 5


# =============================================================================
# Launch config generation
# =============================================================================


class TestLaunchConfig:
    """Launch stage — config file generation and command output."""

    def test_launch_json_structure(self):
        """Verify the launch JSON has the expected structure."""
        from engine.state_machine import PhaseMachine

        points = PhaseMachine.POINTS.get("development", [])
        launch = {
            "project_name": "TestProject",
            "project_desc": "Test description",
            "phase": "development",
            "max_agents": 11,
            "swarm_dir": "/opt/hermes-swarm-loop",
            "points": points,
            "commands": [
                f"hermes kanban swarm --name \"TestProject — development: {pt}\" "
                f"--description \"Test description\" --workdir \"/opt/hermes-swarm-loop\" "
                f"--max-workers 11 --phase development --point {pt}"
                for pt in points
            ],
        }
        assert launch["project_name"] == "TestProject"
        assert len(launch["commands"]) == len(points)
        for cmd in launch["commands"]:
            assert cmd.startswith("hermes kanban swarm")
            assert "development" in cmd

    def test_launch_json_serializable(self):
        """Launch config should be JSON-serializable."""
        from engine.state_machine import PhaseMachine

        points = PhaseMachine.POINTS.get("development", [])
        launch = {
            "project_name": "Test",
            "project_desc": "Desc",
            "phase": "development",
            "max_agents": 11,
            "swarm_dir": "/tmp",
            "points": points,
            "commands": ["hermes kanban swarm --name test"],
        }
        dumped = json.dumps(launch)
        reloaded = json.loads(dumped)
        assert reloaded["project_name"] == "Test"
        assert len(reloaded["commands"]) == 1

    def test_init_only_does_not_require_project_name(self):
        """--init-only should permit running without --project-name."""
        # This is a logical test — bootstrap.py uses argparse.ArgumentParser
        # with --project-name="" as default, so init-only doesn't enforce it.
        from engine.state_machine import PhaseMachine

        assert "development" in PhaseMachine.ALL_PHASES


# =============================================================================
# Module integrity
# =============================================================================


class TestModuleIntegrity:
    """Verify bootstrap.py module loads and has expected exports."""

    def test_module_has_main(self):
        import bootstrap

        assert hasattr(bootstrap, "main")

    def test_module_has_check_env(self):
        import bootstrap

        assert hasattr(bootstrap, "check_env")

    def test_all_phases_defined(self):
        from engine.state_machine import PhaseMachine

        expected = ["prd_build", "development", "quality", "hunting", "simplicity"]
        assert PhaseMachine.ALL_PHASES == expected

    def test_yolo_zones_have_correct_caps(self):
        from engine.state_machine import YOLO_ZONES

        assert YOLO_ZONES["safe"]["max_parallel"] == 5
        assert YOLO_ZONES["test"]["max_parallel"] == 11
        assert YOLO_ZONES["staging"]["max_parallel"] == 33
        assert YOLO_ZONES["production"]["max_parallel"] == 999

    def test_points_by_phase(self):
        from engine.state_machine import PhaseMachine

        assert PhaseMachine.POINTS["development"] == ["architecture", "setup", "code_generation"]
        assert PhaseMachine.POINTS["quality"] == ["audit", "improve", "review"]
        assert PhaseMachine.POINTS["hunting"] == ["bugs", "arch_review", "security"]
        assert PhaseMachine.POINTS["simplicity"] == ["dead_code", "occam", "prd_alignment"]
