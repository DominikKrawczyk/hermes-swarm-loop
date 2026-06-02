"""Tests for Hermes Swarm Loop — Gate 11 Verifier.

Standalone test file for the Gate11Verifier class that validates
11-agent completion handoffs for a point.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.gate_11 import Gate11Verifier, HandoffValidation, GateResult


# ═══════════════════════════════════════════════════════════════════
# HandoffValidation
# ═══════════════════════════════════════════════════════════════════


class TestHandoffValidation:
    def test_minimal_valid(self):
        hv = HandoffValidation(worker_id="a01", valid=True)
        assert hv.worker_id == "a01"
        assert hv.valid is True
        assert hv.errors == []
        assert hv.handoff == {}

    def test_with_errors(self):
        hv = HandoffValidation(worker_id="a02", valid=False, errors=["missing: summary"])
        assert hv.valid is False
        assert "summary" in hv.errors[0]

    def test_with_handoff_data(self):
        hv = HandoffValidation(
            worker_id="a03", valid=True, handoff={"summary": "done", "status": "done"}
        )
        assert hv.handoff["status"] == "done"


# ═══════════════════════════════════════════════════════════════════
# GateResult
# ═══════════════════════════════════════════════════════════════════


class TestGateResult:
    def test_passed_true(self):
        r = GateResult(passed=True, total_agents=11, completed_agents=11, all_done=True)
        assert r.passed is True

    def test_passed_false(self):
        r = GateResult(passed=False, total_agents=11, completed_agents=10, all_done=False)
        assert r.passed is False

    def test_to_dict_includes_all_keys(self):
        r = GateResult(passed=True, total_agents=11, completed_agents=11, all_done=True)
        d = r.to_dict()
        assert d["passed"] is True
        assert d["total_agents"] == 11
        assert d["completed_agents"] == 11
        assert d["all_done"] is True
        assert "errors" in d


# ═══════════════════════════════════════════════════════════════════
# Gate11Verifier — validate_handoff
# ═══════════════════════════════════════════════════════════════════


class TestValidateHandoff:
    def setup_method(self):
        self.v = Gate11Verifier()

    def test_valid_handoff_passes(self):
        h = {"summary": "done", "worker_id": "a01", "point": "setup", "phase": "dev"}
        r = self.v.validate_handoff(h, "a01")
        assert r.valid is True
        assert r.errors == []

    def test_missing_summary(self):
        h = {"worker_id": "a01", "point": "setup", "phase": "dev"}
        r = self.v.validate_handoff(h, "a01")
        assert r.valid is False
        assert any("summary" in e for e in r.errors)

    def test_missing_worker_id(self):
        h = {"summary": "done", "point": "setup", "phase": "dev"}
        r = self.v.validate_handoff(h, "unknown")
        assert r.valid is False
        assert any("worker_id" in e for e in r.errors)

    def test_missing_point(self):
        h = {"summary": "done", "worker_id": "a01", "phase": "dev"}
        r = self.v.validate_handoff(h, "a01")
        assert r.valid is False

    def test_missing_phase(self):
        h = {"summary": "done", "worker_id": "a01", "point": "setup"}
        r = self.v.validate_handoff(h, "a01")
        assert r.valid is False

    def test_wrong_type_summary(self):
        h = {"summary": 123, "worker_id": "a01", "point": "setup", "phase": "dev"}
        r = self.v.validate_handoff(h, "a01")
        assert r.valid is False

    def test_wrong_type_worker_id(self):
        h = {"summary": "done", "worker_id": 42, "point": "setup", "phase": "dev"}
        r = self.v.validate_handoff(h, "a01")
        assert r.valid is False

    def test_all_fields_present_but_empty_string(self):
        """Empty string is still a valid string type."""
        h = {"summary": "", "worker_id": "", "point": "", "phase": ""}
        r = self.v.validate_handoff(h, "a01")
        assert r.valid is True


# ═══════════════════════════════════════════════════════════════════
# Gate11Verifier — verify
# ═══════════════════════════════════════════════════════════════════


class TestVerify:
    def setup_method(self):
        self.v = Gate11Verifier()

    def _handoff(self, worker_id, status="done"):
        return {
            "worker_id": worker_id,
            "summary": "done",
            "point": "code_generation",
            "phase": "development",
            "status": status,
        }

    def test_eleven_all_done_passes(self):
        handoffs = [self._handoff(f"a{i:02d}") for i in range(11)]
        r = self.v.verify(handoffs)
        assert r.passed is True
        assert r.all_done is True
        assert r.completed_agents == 11
        assert r.total_agents == 11

    def test_ten_agents_fails(self):
        handoffs = [self._handoff(f"a{i:02d}") for i in range(10)]
        r = self.v.verify(handoffs)
        assert r.passed is False
        assert r.all_done is False
        assert len(r.errors) > 0
        assert "Not enough" in r.errors[0] or "enough" in r.errors[0]

    def test_zero_handoffs_fails(self):
        r = self.v.verify([])
        assert r.passed is False
        assert r.all_done is False

    def test_not_all_done_when_some_pending(self):
        handoffs = [self._handoff(f"a{i:02d}") for i in range(11)]
        handoffs[0]["status"] = "running"
        r = self.v.verify(handoffs)
        assert r.passed is False
        assert r.all_done is False

    def test_not_all_done_when_some_failed(self):
        handoffs = [self._handoff(f"a{i:02d}") for i in range(11)]
        handoffs[3]["status"] = "failed"
        r = self.v.verify(handoffs)
        assert r.passed is False
        assert r.all_done is False

    def test_invalid_handoff_errors_reported(self):
        handoffs = [self._handoff(f"a{i:02d}") for i in range(11)]
        handoffs[5] = {"worker_id": "a06"}  # missing summary, point, phase
        r = self.v.verify(handoffs)
        assert r.passed is False
        assert len(r.errors) >= 1
        assert any("a06" in e for e in r.errors)

    def test_eleven_with_metadata(self):
        """Additional fields beyond required schema don't cause errors."""
        handoffs = [
            {
                **self._handoff(f"a{i:02d}"),
                "changed_files": ["file1.py"],
                "tests_passed": 42,
            }
            for i in range(11)
        ]
        r = self.v.verify(handoffs)
        assert r.passed is True

    def test_verification_count_tracks_completed(self):
        handoffs = [self._handoff(f"a{i:02d}") for i in range(11)]
        handoffs[0]["status"] = "done"
        handoffs[1]["status"] = "done"
        handoffs[2]["status"] = "running"  # not done
        r = self.v.verify(handoffs)
        assert r.completed_agents == 10  # 11 total - 1 running
        assert r.all_done is False

    def test_more_than_eleven_handoffs_still_passes(self):
        """The gate checks that AT LEAST 11 are done, so 12 should pass."""
        handoffs = [self._handoff(f"a{i:02d}") for i in range(12)]
        r = self.v.verify(handoffs)
        assert r.passed is True
        assert r.total_agents == 12
        assert r.completed_agents == 12

    def test_validations_list_populated(self):
        handoffs = [self._handoff(f"a{i:02d}") for i in range(11)]
        r = self.v.verify(handoffs)
        assert len(r.validations) == 11


# ═══════════════════════════════════════════════════════════════════
# Gate11Verifier — verify_from_json
# ═══════════════════════════════════════════════════════════════════


class TestVerifyFromJson:
    def setup_method(self):
        self.v = Gate11Verifier()

    def test_valid_json_passes(self):
        handoffs = [
            {"worker_id": f"a{i:02d}", "summary": "done", "point": "setup", "phase": "dev", "status": "done"}
            for i in range(11)
        ]
        raw = json.dumps(handoffs)
        r = self.v.verify_from_json(raw)
        assert r.passed is True

    def test_invalid_json_returns_error(self):
        r = self.v.verify_from_json("not valid json")
        assert r.passed is False
        assert any("Invalid JSON" in e for e in r.errors)

    def test_json_array_but_not_eleven(self):
        handoffs = [
            {"worker_id": "a01", "summary": "done", "point": "setup", "phase": "dev", "status": "done"}
        ]
        raw = json.dumps(handoffs)
        r = self.v.verify_from_json(raw)
        assert r.passed is False

    def test_non_array_json(self):
        r = self.v.verify_from_json('{"not": "an array"}')
        assert r.passed is False
        assert any("Expected JSON array" in e for e in r.errors)

    def test_eleven_empty_dicts(self):
        """11 agents but handoffs are empty dicts — valid schema, all
        missing required fields so should fail."""
        raw = json.dumps([{} for _ in range(11)])
        r = self.v.verify_from_json(raw)
        assert r.passed is False
