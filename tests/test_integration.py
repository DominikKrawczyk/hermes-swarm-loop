"""Integration tests for Hermes Swarm Loop — end-to-end flows across all modules.

Tests the full lifecycle:
  1. Phase Machine + Point Machine integration
  2. YOLO Machine + Safety Valve integration
  3. Mastery Gate + Gate 11 Verifier integration
  4. Workspace Manager integration
  5. Synthesizer integration
  6. Full lifecycle: start phase → create points → start → complete → gate evaluate
  7. Edge cases
"""

from __future__ import annotations

import os
import sys
import tempfile
import json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from engine.state_machine import (
    StateDB,
    PhaseMachine,
    PointMachine,
    YOLOMachine,
    ConflictError,
    YOLO_ZONES,
)
from engine.mastery_gate import MasteryGate, ScoreCard, score_from_dict, DIMENSIONS
from engine.gate_11 import Gate11Verifier
from engine.workspace_manager import WorkspaceManager, WorkspaceKind, WorkspaceError
from engine.synthesizer import synthesize, write_artifact

pytest.importorskip("click")
pytest.importorskip("rich")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def state_db():
    """Create a temporary StateDB for testing."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db = StateDB(tmp.name)
    yield db
    try:
        os.unlink(tmp.name)
    except OSError:
        pass


# ===========================================================================
# 1. Phase Machine + Point Machine Integration
# ===========================================================================


class TestPhasePointIntegration:
    """Integration tests for PhaseMachine + PointMachine working together."""

    def test_create_and_start_point_in_phase(self, state_db):
        """Full point lifecycle: create (todo) → start (running) → complete (done)."""
        pm = PhaseMachine(state_db)
        ptm = PointMachine(state_db)

        pm.start_phase("development")

        # Create point (todo)
        entry = ptm.create_point("development", "architecture", agent_count=11)
        assert entry.phase == "development"
        assert entry.point == "architecture"
        assert entry.agent_count == 11
        assert entry.status == "todo"  # Points start in todo

        # Start point (running)
        entry = ptm.start_point("development", "architecture")
        assert entry.status == "running"
        assert entry.started_at is not None

        # Complete point (done)
        entry = ptm.complete_point("development", "architecture")
        assert entry.status == "done"
        assert entry.completed_at is not None

    def test_create_all_points_in_phase(self, state_db):
        """Create all 3 points for development phase."""
        pm = PhaseMachine(state_db)
        ptm = PointMachine(state_db)
        pm.start_phase("development")

        for point, agents in [("architecture", 11), ("setup", 11), ("code_generation", 11)]:
            entry = ptm.create_point("development", point, agent_count=agents)
            assert entry.status == "todo"

        points = ptm.get_points_for_phase("development")
        assert len(points) == 3
        assert [p.point for p in points] == ["architecture", "setup", "code_generation"]

    def test_start_and_complete_all_points(self, state_db):
        """Start and complete all 3 points through the lifecycle."""
        pm = PhaseMachine(state_db)
        ptm = PointMachine(state_db)
        pm.start_phase("development")

        for point in ["architecture", "setup", "code_generation"]:
            ptm.create_point("development", point)
            ptm.start_point("development", point)
            assert ptm.get_point("development", point).status == "running"
            ptm.complete_point("development", point)
            assert ptm.get_point("development", point).status == "done"

    def test_complete_point_from_todo(self, state_db):
        """complete_point also works directly from todo (skip start)."""
        pm = PhaseMachine(state_db)
        ptm = PointMachine(state_db)
        pm.start_phase("development")
        ptm.create_point("development", "setup")
        entry = ptm.complete_point("development", "setup")
        assert entry.status == "done"

    def test_phase_idempotency(self, state_db):
        """Starting an already-running phase is idempotent."""
        pm = PhaseMachine(state_db)
        pm.start_phase("hunting")
        pm.start_phase("hunting")
        entry = pm.get_phase("hunting")
        assert entry.status == "running"

    def test_complete_phase_after_all_points(self, state_db):
        """Complete a phase after all its points are done."""
        pm = PhaseMachine(state_db)
        ptm = PointMachine(state_db)
        pm.start_phase("quality")
        for point in ["audit", "improve", "review"]:
            ptm.create_point("quality", point)
            ptm.complete_point("quality", point)  # works from todo too
        entry = pm.complete_phase("quality")
        assert entry.status == "done"
        assert entry.completed_at is not None

    def test_phase_requires_running_to_complete(self, state_db):
        """Completing a phase that isn't running raises ConflictError."""
        pm = PhaseMachine(state_db)
        with pytest.raises(ConflictError, match="not found|not in running"):
            pm.complete_phase("development")

    def test_all_phases_order(self, state_db):
        """PhaseMachine.ALL_PHASES are in the correct order."""
        pm = PhaseMachine(state_db)
        for phase in pm.ALL_PHASES:
            pm.start_phase(phase)
        phases = pm.all_phases()
        assert len(phases) == 5
        order = [p.phase for p in phases]
        assert order == ["prd_build", "development", "quality", "hunting", "simplicity"]

    def test_invalid_phase_name(self, state_db):
        pm = PhaseMachine(state_db)
        with pytest.raises(ValueError, match="Unknown phase"):
            pm.start_phase("nonexistent_phase")


# ===========================================================================
# 2. YOLO Machine + Safety Valve Integration
# ===========================================================================


class TestYOLOIntegration:
    """Integration tests for YOLO zone management with state machine."""

    def test_yolo_zone_effects_state_machine(self, state_db):
        """Setting a YOLO zone updates the state machine behaviour."""
        ym = YOLOMachine(state_db)

        initial = ym.get_state()
        assert initial.zone == "safe"
        assert initial.max_parallel == 5
        assert initial.auto_approve is False

        for zone, expected_parallel in [
            ("test", 11),
            ("staging", 33),
            ("production", 999),
            ("safe", 5),
        ]:
            state = ym.set_zone(zone)
            assert state.zone == zone
            assert state.max_parallel == expected_parallel
            assert state.auto_approve == (zone in ("staging", "production"))

    def test_safety_valve_triggers_at_zone_max_errors(self, state_db):
        """Safety valve activates per zone max_errors."""
        ym = YOLOMachine(state_db)
        ym.set_zone("safe")  # max_errors=3 for safe

        for _ in range(3):
            ym.increment_errors()

        state = ym.get_state()
        assert state.safety_valve_active is True
        assert state.max_parallel == 1
        assert state.auto_approve is False

    def test_safety_valve_zone_test(self, state_db):
        """Safety valve activates at 5 errors for test zone."""
        ym = YOLOMachine(state_db)
        ym.set_zone("test")  # max_errors=5

        for _ in range(5):
            ym.increment_errors()

        assert ym.get_state().safety_valve_active is True

    def test_reset_safety_valve(self, state_db):
        """Resetting the safety valve restores zone's defaults."""
        ym = YOLOMachine(state_db)
        ym.set_zone("test")

        for _ in range(5):
            ym.increment_errors()

        assert ym.get_state().safety_valve_active is True

        ym.reset_safety_valve()
        state = ym.get_state()
        assert state.safety_valve_active is False
        assert state.consecutive_errors == 0
        assert state.zone == "test"  # Zone preserved

    def test_yolo_logs_events(self, state_db):
        """YOLO operations produce audit events."""
        ym = YOLOMachine(state_db)
        ym.set_zone("production")

        with state_db.cursor() as cur:
            cur.execute("SELECT kind, payload FROM event_log WHERE kind='yolo_zone_set'")
            rows = cur.fetchall()
        assert len(rows) >= 1
        assert any("production" in json.loads(r["payload"]).get("zone", "") for r in rows)

    def test_yolo_all_zones(self, state_db):
        """All YOLO_ZONES are configurable through the machine."""
        ym = YOLOMachine(state_db)
        for zone in YOLO_ZONES:
            state = ym.set_zone(zone)
            assert state.zone == zone

    def test_admit_checks_capacity(self, state_db):
        """admit() respects max_parallel."""
        ym = YOLOMachine(state_db)
        ym.set_zone("test")  # max_parallel=11
        assert ym.admit(current_runners=10) is True
        assert ym.admit(current_runners=11) is False
        assert ym.admit(current_runners=100) is False

    def test_admit_safety_valve(self, state_db):
        """admit() returns False when safety valve is active."""
        ym = YOLOMachine(state_db)
        ym.activate_safety_valve()
        assert ym.admit(current_runners=0) is False


# ===========================================================================
# 3. Mastery Gate + Gate 11 Verifier Integration
# ===========================================================================


class TestMasteryGateIntegration:
    """Integration tests for MasteryGate + Gate11Verifier working together."""

    def test_gate_11_passes_with_valid_handoffs(self):
        """Gate 11 passes with 11 valid handoffs."""
        verifier = Gate11Verifier()
        handoffs = [
            {"worker_id": f"code_gen_{i:02d}", "point": "code_generation",
             "phase": "development", "summary": f"Agent {i} output", "status": "done"}
            for i in range(1, 12)
        ]
        result = verifier.verify(handoffs)
        assert result.passed is True
        assert result.completed_agents == 11
        assert result.all_done is True

    def test_gate_11_fails_with_fewer_agents(self):
        """Gate 11 fails with fewer than 11 agents."""
        verifier = Gate11Verifier()
        handoffs = [
            {"worker_id": f"agent_{i:02d}", "point": "test", "phase": "dev",
             "summary": f"Agent {i}", "status": "done"}
            for i in range(1, 6)
        ]
        result = verifier.verify(handoffs)
        assert result.passed is False
        assert any("Not enough agents" in e for e in result.errors)

    def test_gate_11_detects_missing_fields(self):
        """Handoffs missing required fields are flagged."""
        verifier = Gate11Verifier()
        handoffs = [
            {"worker_id": "agent_01", "point": "test", "phase": "dev",
             "summary": "ok", "status": "done"},
            {"point": "test", "status": "done"},  # missing worker_id, phase, summary
        ]
        result = verifier.verify(handoffs)
        assert result.passed is False

    def test_mastery_gate_scoring(self):
        """MasteryGate evaluates multiple agents correctly."""
        mg = MasteryGate()
        scores = [
            ScoreCard(correctness=0.85, safety=0.80, test_coverage=0.75,
                      consistency=0.80, diversity=0.70, efficiency=0.85, clarity=0.90),
            ScoreCard(correctness=0.80, safety=0.85, test_coverage=0.70,
                      consistency=0.75, diversity=0.75, efficiency=0.80, clarity=0.85),
        ]
        result = mg.evaluate(scores)
        assert result.weighted_total > 0.50
        assert hasattr(result, "verdict")

    def test_mastery_gate_pass(self):
        """High scores should PASS."""
        mg = MasteryGate()
        scores = [
            ScoreCard(correctness=0.95, safety=0.95, test_coverage=0.90,
                      consistency=0.90, diversity=0.85, efficiency=0.95, clarity=0.95),
        ]
        result = mg.evaluate(scores)
        assert result.weighted_total >= 0.70
        assert result.verdict == "PASS"

    def test_mastery_gate_block(self):
        """Very low scores should BLOCK."""
        mg = MasteryGate()
        scores = [
            ScoreCard(correctness=0.20, safety=0.15, test_coverage=0.10,
                      consistency=0.20, diversity=0.10, efficiency=0.15, clarity=0.20),
        ]
        result = mg.evaluate(scores)
        assert result.weighted_total < 0.30
        assert result.verdict == "BLOCK"

    def test_gate_json_parsing(self):
        """Gate11Verifier parses JSON input correctly."""
        verifier = Gate11Verifier()
        raw = json.dumps([
            {"worker_id": "agent_01", "point": "code", "phase": "development",
             "summary": "Done", "status": "done"},
        ])
        result = verifier.verify_from_json(raw)
        assert result.passed is False
        assert result.total_agents == 11

    def test_gate_bad_json(self):
        """Invalid JSON is caught gracefully."""
        verifier = Gate11Verifier()
        result = verifier.verify_from_json("this is not json")
        assert result.passed is False
        assert "Invalid JSON" in " ".join(result.errors)

    def test_gate_non_list_json(self):
        """Non-array JSON is caught."""
        verifier = Gate11Verifier()
        result = verifier.verify_from_json('{"agent": "one"}')
        assert result.passed is False
        assert "Expected JSON array" in " ".join(result.errors)

    def test_score_from_dict_roundtrip(self):
        """Agent scores round-trip through dict serialization."""
        original = ScoreCard(correctness=0.85, safety=0.80, test_coverage=0.75,
                              consistency=0.80, diversity=0.70, efficiency=0.85, clarity=0.90)
        d = original.to_dict()
        restored = score_from_dict(d["scores"])
        for dim in DIMENSIONS:
            assert getattr(restored, dim) == getattr(original, dim)

    def test_mastery_gate_diversification(self):
        """check_diversification identifies common gaps."""
        mg = MasteryGate()
        card = ScoreCard(correctness=0.85, safety=0.60, test_coverage=0.80,
                          consistency=0.85, diversity=0.40, efficiency=0.85, clarity=0.90)
        gaps = mg.check_diversification(card)
        assert len(gaps) >= 1
        gap_texts = " ".join(gaps).lower()
        assert "diversity" in gap_texts or "safety" in gap_texts


# ===========================================================================
# 4. Workspace Manager Integration
# ===========================================================================


class TestWorkspaceIntegration:
    """Integration tests for WorkspaceManager."""

    def test_scratch_workspace_lifecycle(self):
        """Create, verify, and teardown a scratch workspace."""
        import tempfile as tf
        with tf.TemporaryDirectory() as root:
            wm = WorkspaceManager(workspace_root=root)
            ws = wm.setup("scratch", task_id="t_int_test", label="integration-test")
            assert ws.path.exists()
            assert "t_int_test" in str(ws.path)

            test_file = ws.path / "test.txt"
            test_file.write_text("integration test")
            assert test_file.exists()

            wm.teardown(ws, cleanup=True)
            assert ws.path.exists() is False

    def test_dir_workspace(self):
        """Create a dir workspace at a known path."""
        with tempfile.TemporaryDirectory() as root:
            ws_path = os.path.join(root, "my-workspace")
            wm = WorkspaceManager()
            ws = wm.setup("dir", dir_path=ws_path, label="dir-test")
            assert ws.path.exists()
            assert ws.path.is_dir()
            assert ws.kind == WorkspaceKind.DIR

    def test_workspace_resolve_kind_tokens(self):
        """WorkspaceManager resolves kind tokens correctly."""
        wm = WorkspaceManager()
        assert wm.resolve_kind_from_token("scratch") == WorkspaceKind.SCRATCH
        assert wm.resolve_kind_from_token("worktree") == WorkspaceKind.WORKTREE
        assert wm.resolve_kind_from_token("dir:/opt/data") == WorkspaceKind.DIR

        with pytest.raises(WorkspaceError):
            wm.resolve_kind_from_token("invalid_kind")

    def test_workspace_resolve_path_tokens(self):
        """WorkspaceManager resolves path tokens correctly."""
        wm = WorkspaceManager()
        assert wm.resolve_path_from_token("scratch") is None
        result = wm.resolve_path_from_token("dir:/opt/data")
        assert result == Path("/opt/data")

        with pytest.raises(WorkspaceError):
            wm.resolve_path_from_token("dir:relative/path")


# ===========================================================================
# 5. Synthesizer Integration
# ===========================================================================


class TestSynthesizerIntegration:
    """Integration tests for the output synthesizer."""

    def test_synthesizer_dedup(self):
        """Synthesizer deduplicates identical findings."""
        outputs = [
            {"agent_id": "a1", "output": {"findings": [{"id": 1, "desc": "Critical bug"}]},
             "status": "completed"},
            {"agent_id": "a2", "output": {"findings": [{"id": 1, "desc": "Critical bug"}]},
             "status": "completed"},
            {"agent_id": "a3", "output": {"findings": [{"id": 2, "desc": "Minor issue"}]},
             "status": "completed"},
        ]
        merged = synthesize(outputs)
        assert len(merged["merged_findings"]) == 2
        assert merged["completed_count"] == 3
        assert merged["dedup_count"] == 1

    def test_synthesizer_respects_failed_agents(self):
        """Failed agents are counted correctly."""
        outputs = [
            {"agent_id": "a1", "output": {"findings": [{"id": 1}]}, "status": "completed"},
            {"agent_id": "a2", "output": {}, "status": "failed"},
            {"agent_id": "a3", "output": {"findings": [{"id": 2}]}, "status": "completed"},
        ]
        merged = synthesize(outputs)
        assert merged["completed_count"] == 2
        assert merged["failed_count"] == 1
        assert len(merged["merged_findings"]) == 2

    def test_synthesizer_write_artifact(self):
        """write_artifact creates a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmp:
            output = {"merged_findings": [], "agent_count": 3, "completed_count": 3}
            path = write_artifact(output, os.path.join(tmp, "artifact.json"))
            assert os.path.exists(path)
            with open(path) as f:
                loaded = json.load(f)
            assert loaded["agent_count"] == 3

    def test_synthesizer_empty_inputs(self):
        """Empty input list produces minimal output."""
        merged = synthesize([])
        assert merged["agent_count"] == 0
        assert merged["completed_count"] == 0
        assert merged["merged_findings"] == []


# ===========================================================================
# 6. Full Lifecycle Integration
# ===========================================================================


class TestFullLifecycle:
    """End-to-end integration: phase → point → gate → synthesize."""

    def test_full_development_cycle(self, state_db):
        """Simulate a complete development cycle."""
        pm = PhaseMachine(state_db)
        ptm = PointMachine(state_db)
        ym = YOLOMachine(state_db)

        ym.set_zone("test")
        assert ym.get_state().zone == "test"

        pm.start_phase("development")

        for point in ["architecture", "setup", "code_generation"]:
            ptm.create_point("development", point, agent_count=11)
            ptm.start_point("development", point)
            ptm.complete_point("development", point)

        entry = pm.complete_phase("development")
        assert entry.status == "done"
        assert entry.completed_at is not None

        phase = pm.get_phase("development")
        assert phase.status == "done"

    def test_complete_phase_with_all_points_done(self, state_db):
        """Phase completes only after all points are done."""
        pm = PhaseMachine(state_db)
        ptm = PointMachine(state_db)
        pm.start_phase("quality")
        for point in ["audit", "improve", "review"]:
            ptm.create_point("quality", point)
        # Complete all
        for point in ["audit", "improve", "review"]:
            ptm.complete_point("quality", point)
        entry = pm.complete_phase("quality")
        assert entry.status == "done"

    def test_all_event_logging(self, state_db):
        """Verify all operations produce proper event log entries."""
        pm = PhaseMachine(state_db)
        ptm = PointMachine(state_db)
        ym = YOLOMachine(state_db)

        pm.start_phase("simplicity")
        ptm.create_point("simplicity", "dead_code")
        ptm.complete_point("simplicity", "dead_code")
        pm.complete_phase("simplicity")
        ym.set_zone("production")

        with state_db.cursor() as cur:
            cur.execute("SELECT DISTINCT kind FROM event_log")
            kinds = {row["kind"] for row in cur.fetchall()}
        assert "phase_started" in kinds
        assert "phase_completed" in kinds
        assert "point_created" in kinds
        assert "point_completed" in kinds
        assert "yolo_zone_set" in kinds

    def test_fail_point_and_recover(self, state_db):
        """Fail a point, then re-create and succeed."""
        pm = PhaseMachine(state_db)
        ptm = PointMachine(state_db)
        pm.start_phase("quality")

        ptm.create_point("quality", "audit")
        ptm.fail_point("quality", "audit", "test failure")
        failed = ptm.get_point("quality", "audit")
        assert failed.status == "failed"

        ptm.create_point("quality", "audit")  # re-create (upsert)
        ptm.start_point("quality", "audit")   # todo -> running
        ptm.complete_point("quality", "audit")
        entry = ptm.get_point("quality", "audit")
        assert entry.status == "done"


# ===========================================================================
# 7. Edge Cases
# ===========================================================================


class TestEdgeCases:
    """Edge case and boundary tests."""

    def test_get_nonexistent_point(self, state_db):
        """Getting a non-existent point returns None."""
        ptm = PointMachine(state_db)
        assert ptm.get_point("ghost_phase", "ghost_point") is None

    def test_get_nonexistent_phase(self, state_db):
        pm = PhaseMachine(state_db)
        assert pm.get_phase("ghost_phase") is None

    def test_yolo_unknown_zone(self, state_db):
        ym = YOLOMachine(state_db)
        with pytest.raises(ValueError, match="Unknown YOLO zone"):
            ym.set_zone("hyperdrive")

    def test_empty_point_list(self, state_db):
        ptm = PointMachine(state_db)
        assert ptm.get_points_for_phase("development") == []

    def test_yolo_state_after_zone_change(self, state_db):
        ym = YOLOMachine(state_db)
        ym.set_zone("production")
        state = ym.get_state()
        assert state.zone == "production"
        assert state.max_parallel == 999
        assert state.auto_approve is True

    def test_point_status_transitions(self, state_db):
        """Point goes through all statuses: todo → running → done."""
        pm = PhaseMachine(state_db)
        ptm = PointMachine(state_db)
        pm.start_phase("development")

        entry = ptm.create_point("development", "arch")
        assert entry.status == "todo"

        entry = ptm.start_point("development", "arch")
        assert entry.status == "running"

        entry = ptm.complete_point("development", "arch")
        assert entry.status == "done"

    def test_cannot_start_completed_point(self, state_db):
        """Starting a done point raises ConflictError."""
        pm = PhaseMachine(state_db)
        ptm = PointMachine(state_db)
        pm.start_phase("development")
        ptm.create_point("development", "arch")
        ptm.complete_point("development", "arch")
        with pytest.raises(ConflictError, match="not in todo"):
            ptm.start_point("development", "arch")

    def test_increment_errors_per_zone(self, state_db):
        """Different zones have different error thresholds."""
        ym = YOLOMachine(state_db)

        # safe zone: max_errors=3
        ym.set_zone("safe")
        for _ in range(3):
            ym.increment_errors()
        assert ym.get_state().safety_valve_active is True
        ym.reset_safety_valve()

        # production zone: max_errors=999 (never trips)
        ym.set_zone("production")
        for _ in range(100):
            ym.increment_errors()
        assert ym.get_state().safety_valve_active is False
