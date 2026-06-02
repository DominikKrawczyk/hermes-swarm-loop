"""Tests for Hermes Swarm Loop — Engine state_machine module.
Matches the actual API as built by Phase 1 code generation agents.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.state_machine import (
    StateDB, PhaseMachine, PointMachine, YOLOMachine,
    PhaseEntry, PointEntry, YOLOState, ConflictError,
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
            assert entry.status == "running"
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
