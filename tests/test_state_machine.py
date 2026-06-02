"""Tests for Hermes Swarm Loop — Engine state_machine module.
Matches the actual API as built by Phase 1 code generation agents.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.state_machine import (
    ConflictError,
    PhaseMachine,
    PointMachine,
    StateDB,
    YOLOMachine,
)


def _make_db():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    return StateDB(tmp.name), tmp.name


class TestStateDB:
    def test_creates_tables(self):
        db, path = _make_db()
        try:
            with db.cursor() as cur:
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = {row["name"] for row in cur.fetchall()}
            assert "phase_state" in tables
            assert "point_state" in tables
            assert "yolo_state" in tables
            assert "event_log" in tables
            assert "launch_config" in tables
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_cursor_commit(self):
        db, path = _make_db()
        try:
            with db.cursor() as cur:
                cur.execute("INSERT INTO phase_state (phase, status) VALUES ('test', 'todo')")
                cur.connection.commit()
            with db.cursor() as cur:
                cur.execute("SELECT COUNT(*) as cnt FROM phase_state")
                assert cur.fetchone()["cnt"] == 1
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_log_event(self):
        db, path = _make_db()
        try:
            db.log_event("test_event", {"detail": "hello"})
            with db.cursor() as cur:
                cur.execute("SELECT kind, payload FROM event_log WHERE kind='test_event'")
                row = cur.fetchone()
                assert row is not None
                assert row["kind"] == "test_event"
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_yolo_default_inserted(self):
        db, path = _make_db()
        try:
            with db.cursor() as cur:
                cur.execute("SELECT zone, auto_approve, max_parallel FROM yolo_state WHERE id=1")
                row = cur.fetchone()
                assert row is not None
                assert row["zone"] == "safe"
                assert row["auto_approve"] == 0
                assert row["max_parallel"] == 5
        finally:
            try: os.unlink(path)
            except OSError: pass


class TestPhaseMachine:
    def test_start_phase(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            entry = pm.start_phase("development")
            assert entry.phase == "development"
            assert entry.status == "running"
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_get_phase(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            entry = pm.get_phase("development")
            assert entry is not None
            assert entry.phase == "development"
            assert entry.status == "running"
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_get_phase_not_found(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            assert pm.get_phase("nonexistent") is None
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_complete_phase(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            entry = pm.complete_phase("development")
            assert entry.status == "done"
            assert entry.completed_at is not None
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_all_phases(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            assert pm.all_phases() == []
            pm.start_phase("development")
            pm.start_phase("quality")
            phases = pm.all_phases()
            assert len(phases) == 2
            assert [p.phase for p in phases] == ["development", "quality"]
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_invalid_phase_raises(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            import pytest
            with pytest.raises(ValueError, match="Unknown phase"):
                pm.start_phase("invalid_phase_name")
        finally:
            try: os.unlink(path)
            except OSError: pass


class TestPointMachine:
    def test_create_point(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            ptm = PointMachine(db)
            entry = ptm.create_point("development", "setup", agent_count=11)
            assert entry.phase == "development"
            assert entry.point == "setup"
            assert entry.agent_count == 11
            assert entry.status == "todo"
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_get_point(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            ptm = PointMachine(db)
            ptm.create_point("development", "architecture")
            entry = ptm.get_point("development", "architecture")
            assert entry is not None
            assert entry.point == "architecture"
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_get_point_not_found(self):
        db, path = _make_db()
        try:
            ptm = PointMachine(db)
            assert ptm.get_point("development", "ghost") is None
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_complete_point(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            ptm = PointMachine(db)
            ptm.create_point("development", "setup")
            ptm.start_point("development", "setup")
            entry = ptm.complete_point("development", "setup")
            assert entry.status == "done"
            assert entry.completed_at is not None
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_get_points_for_phase(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            ptm = PointMachine(db)
            ptm.create_point("development", "architecture")
            ptm.create_point("development", "setup")
            points = ptm.get_points_for_phase("development")
            assert len(points) == 2
            assert [p.point for p in points] == ["architecture", "setup"]
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_all_points(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            ptm = PointMachine(db)
            ptm.create_point("development", "architecture")
            ptm.create_point("development", "setup")
            all_pts = ptm.all_points()
            assert len(all_pts) == 2
        finally:
            try: os.unlink(path)
            except OSError: pass


class TestYOLOMachine:
    def test_initial_state(self):
        db, path = _make_db()
        try:
            ym = YOLOMachine(db)
            state = ym.get_state()
            assert state.zone == "safe"
            assert state.max_parallel == 5
            assert state.auto_approve == False
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_set_zone(self):
        db, path = _make_db()
        try:
            ym = YOLOMachine(db)
            ym.set_zone("test")
            state = ym.get_state()
            assert state.zone == "test"
            assert state.auto_approve == False
            assert state.max_parallel == 11
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_set_zone_staging(self):
        db, path = _make_db()
        try:
            ym = YOLOMachine(db)
            ym.set_zone("staging")
            state = ym.get_state()
            assert state.zone == "staging"
            assert state.max_parallel == 33
            assert state.auto_approve == True
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_safety_valve(self):
        db, path = _make_db()
        try:
            ym = YOLOMachine(db)
            assert ym.get_state().safety_valve_active == False
            ym.activate_safety_valve()
            assert ym.get_state().safety_valve_active == True
            ym.reset_safety_valve()
            assert ym.get_state().safety_valve_active == False
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_increment_errors(self):
        db, path = _make_db()
        try:
            ym = YOLOMachine(db)
            initial = ym.get_state().consecutive_errors
            ym.increment_errors()
            assert ym.get_state().consecutive_errors == initial + 1
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_set_zone_production(self):
        db, path = _make_db()
        try:
            ym = YOLOMachine(db)
            ym.set_zone("production")
            state = ym.get_state()
            assert state.zone == "production"
            assert state.auto_approve == True
            assert state.max_parallel == 999
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_invalid_zone_raises(self):
        db, path = _make_db()
        try:
            ym = YOLOMachine(db)
            import pytest
            with pytest.raises(ValueError, match="Unknown YOLO zone"):
                ym.set_zone("nonexistent")
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_repr(self):
        db, path = _make_db()
        try:
            ym = YOLOMachine(db)
            assert repr(ym.get_state()).startswith("YOLOState")
        finally:
            try: os.unlink(path)
            except OSError: pass


class TestPhaseMachineExtended:
    """Tests for fail_phase and archive_phase methods."""

    def test_fail_phase_from_running(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            entry = pm.fail_phase("development", "infra outage")
            assert entry.status == "failed"
            assert entry.completed_at is not None
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_fail_phase_not_running_raises(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            import pytest
            with pytest.raises(ConflictError):
                pm.fail_phase("development")  # not started
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_fail_phase_from_done_raises(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            pm.complete_phase("development")
            import pytest
            with pytest.raises(ConflictError):
                pm.fail_phase("development")
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_archive_phase_from_done(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            pm.complete_phase("development")
            entry = pm.archive_phase("development")
            assert entry.status == "archived"
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_archive_phase_from_failed(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            pm.fail_phase("development")
            entry = pm.archive_phase("development")
            assert entry.status == "archived"
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_archive_phase_not_terminal_raises(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            import pytest
            with pytest.raises(ConflictError):
                pm.archive_phase("development")  # still running
        finally:
            try: os.unlink(path)
            except OSError: pass


class TestPointMachineExtended:
    """Tests for start_point and fail_point methods."""

    def test_start_point_from_todo(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            pt_m = PointMachine(db)
            # create_point creates as 'todo', start_point transitions to 'running'
            pt_m.create_point("development", "setup")
            entry = pt_m.start_point("development", "setup")
            assert entry.status == "running"
            assert entry.started_at is not None
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_start_point_already_running_raises(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            pt_m = PointMachine(db)
            # create_point -> todo, start_point -> running
            pt_m.create_point("development", "setup")
            pt_m.start_point("development", "setup")
            import pytest
            with pytest.raises(ConflictError):
                pt_m.start_point("development", "setup")  # already running
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_fail_point_from_running(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            pt_m = PointMachine(db)
            pt_m.create_point("development", "setup")
            pt_m.start_point("development", "setup")  # todo -> running
            entry = pt_m.fail_point("development", "setup", "test failure")
            assert entry.status == "failed"
            assert entry.completed_at is not None
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_fail_point_done_raises(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            pt_m = PointMachine(db)
            pt_m.create_point("development", "setup")
            pt_m.start_point("development", "setup")  # todo -> running
            pt_m.complete_point("development", "setup")  # running -> done
            import pytest
            with pytest.raises(ConflictError):
                pt_m.fail_point("development", "setup")
        finally:
            try: os.unlink(path)
            except OSError: pass


class TestYOLOMachineExtended:
    """Tests for admit() and zone-specific error thresholds."""

    def test_admit_safe_zone_below_parallel(self):
        db, path = _make_db()
        try:
            ym = YOLOMachine(db)
            ym.set_zone("safe")
            assert ym.admit(0) is True
            assert ym.admit(3) is True
            assert ym.admit(4) is True
            assert ym.admit(5) is False  # at capacity
            assert ym.admit(6) is False  # over capacity
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_admit_test_zone(self):
        db, path = _make_db()
        try:
            ym = YOLOMachine(db)
            ym.set_zone("test")
            assert ym.admit(10) is True
            assert ym.admit(11) is False  # at capacity
            assert ym.admit(20) is False
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_admit_staging_zone(self):
        db, path = _make_db()
        try:
            ym = YOLOMachine(db)
            ym.set_zone("staging")
            assert ym.admit(32) is True
            assert ym.admit(33) is False  # at capacity
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_admit_production_zone(self):
        db, path = _make_db()
        try:
            ym = YOLOMachine(db)
            ym.set_zone("production")
            assert ym.admit(500) is True
            assert ym.admit(998) is True
            assert ym.admit(999) is False  # at capacity
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_admit_safety_valve_blocked(self):
        db, path = _make_db()
        try:
            ym = YOLOMachine(db)
            ym.activate_safety_valve()
            assert ym.admit(0) is False
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_admit_safety_valve_reset(self):
        db, path = _make_db()
        try:
            ym = YOLOMachine(db)
            ym.activate_safety_valve()
            assert ym.admit(0) is False
            ym.reset_safety_valve()
            assert ym.admit(0) is True
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_admit_explicit_zone_override(self):
        db, path = _make_db()
        try:
            ym = YOLOMachine(db)
            ym.set_zone("test")
            # override with 'safe' zone even though current is 'test'
            assert ym.admit(4, zone_name="safe") is True
            assert ym.admit(5, zone_name="safe") is False
        finally:
            try: os.unlink(path)
            except OSError: pass


class TestPhaseLifecycle:
    """Tests for PhaseMachine fail_phase and archive_phase."""

    def test_fail_phase(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            entry = pm.fail_phase("development", "critical bug")
            assert entry.status == "failed"
            assert entry.completed_at is not None
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_fail_phase_not_running_raises(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            import pytest
            with pytest.raises(ConflictError, match="not in running"):
                pm.fail_phase("development")
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_archive_done_phase(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("quality")
            pm.complete_phase("quality")
            entry = pm.archive_phase("quality")
            assert entry.status == "archived"
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_archive_failed_phase(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("quality")
            pm.fail_phase("quality")
            entry = pm.archive_phase("quality")
            assert entry.status == "archived"
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_archive_running_phase_raises(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            import pytest
            with pytest.raises(ConflictError, match="not done or failed"):
                pm.archive_phase("development")
        finally:
            try: os.unlink(path)
            except OSError: pass


class TestPointLifecycle:
    """Tests for PointMachine start_point and fail_point."""

    def test_start_point(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            ptm = PointMachine(db)
            # Create point via raw SQL in 'todo' state to exercise start_point
            with db.cursor() as c:
                c.execute(
                    "INSERT INTO point_state (phase, point, status, agent_count, started_at, version) "
                    "VALUES (?, ?, 'todo', 11, NULL, 1)",
                    ("development", "architecture")
                )
            entry = ptm.start_point("development", "architecture")
            assert entry.status == "running"
            assert entry.started_at is not None
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_start_point_already_running_raises(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            ptm = PointMachine(db)
            ptm.create_point("development", "architecture")
            ptm.start_point("development", "architecture")
            import pytest
            with pytest.raises(ConflictError, match="not in todo"):
                ptm.start_point("development", "architecture")
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_fail_point(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            ptm = PointMachine(db)
            ptm.create_point("development", "setup")
            ptm.start_point("development", "setup")
            entry = ptm.fail_point("development", "setup", "implementation stuck")
            assert entry.status == "failed"
            assert entry.completed_at is not None
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_fail_point_not_running_raises(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            ptm = PointMachine(db)
            ptm.create_point("development", "setup")
            ptm.start_point("development", "setup")
            ptm.complete_point("development", "setup")
            import pytest
            with pytest.raises(ConflictError, match="not running"):
                ptm.fail_point("development", "setup")
        finally:
            try: os.unlink(path)
            except OSError: pass


class TestYOLOAdmit:
    """Tests for YOLOMachine.admit() admission control."""

    def test_admit_safe_zone_under_limit(self):
        db, path = _make_db()
        try:
            ym = YOLOMachine(db)
            assert ym.get_state().zone == "safe"
            assert ym.admit(0) is True
            assert ym.admit(4) is True
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_admit_safe_zone_at_limit(self):
        db, path = _make_db()
        try:
            ym = YOLOMachine(db)
            assert ym.admit(5) is False
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_admit_with_explicit_zone(self):
        db, path = _make_db()
        try:
            ym = YOLOMachine(db)
            assert ym.admit(0, zone_name="production") is True
            assert ym.admit(999, zone_name="production") is False
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_admit_rejects_when_safety_valve_active(self):
        db, path = _make_db()
        try:
            ym = YOLOMachine(db)
            ym.activate_safety_valve()
            assert ym.admit(0) is False
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_admit_respects_zone_max_errors(self):
        db, path = _make_db()
        try:
            ym = YOLOMachine(db)
            # safe zone has max_errors=3
            ym.increment_errors()  # 1
            ym.increment_errors()  # 2
            ym.increment_errors()  # 3 -> should trip valve (safe zone max_errors=3)
            assert ym.get_state().safety_valve_active is True
            assert ym.admit(0) is False
        finally:
            try: os.unlink(path)
            except OSError: pass


class TestStateMachineEdgeCases:
    """Remaining edge cases for complete_point and fail_point ConflictError paths."""

    def test_complete_point_already_done_raises(self):
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            ptm = PointMachine(db)
            ptm.create_point("development", "p1")
            ptm.start_point("development", "p1")
            ptm.complete_point("development", "p1")  # running -> done
            import pytest
            # done -> done is not allowed (not running/todo)
            with pytest.raises(ConflictError, match="Cannot complete"):
                ptm.complete_point("development", "p1")
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_complete_point_nonexistent_raises(self):
        db, path = _make_db()
        try:
            from engine.state_machine import ConflictError
            import pytest
            pm = PhaseMachine(db)
            pm.start_phase("development")
            ptm = PointMachine(db)
            with pytest.raises(ConflictError, match="Cannot complete"):
                ptm.complete_point("development", "nonexistent")
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_fail_point_nonexistent_raises(self):
        db, path = _make_db()
        try:
            import pytest
            pm = PhaseMachine(db)
            pm.start_phase("development")
            ptm = PointMachine(db)
            with pytest.raises(ConflictError, match="Cannot fail"):
                ptm.fail_point("development", "ghost")
        finally:
            try: os.unlink(path)
            except OSError: pass

    def test_archive_phase_lifecycle(self):
        """archive_phase works when phase is done."""
        db, path = _make_db()
        try:
            pm = PhaseMachine(db)
            pm.start_phase("development")
            pm.complete_phase("development")  # running -> done
            pm.archive_phase("development")    # done -> archived
            entry = pm.get_phase("development")
            assert entry is not None
            assert entry.status == "archived"
        finally:
            try: os.unlink(path)
            except OSError: pass
