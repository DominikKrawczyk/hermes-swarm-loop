"""Tests for Hermes Swarm Loop — Gate Verifier."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.gate_verifier import (
    AgentCompletionStatus,
    GateVerifier,
    HandoffSchema,
    HandoffValidationResult,
)


class TestGateVerifier:
    def setup_method(self):
        self.verifier = GateVerifier()

    def _make_schema(self, **overrides):
        return HandoffSchema(
            id=overrides.get("id", 1),
            name=overrides.get("name", "test-schema"),
            properties=overrides.get("properties", {
                "summary": {"type": "string"},
                "worker_id": {"type": "string"},
            }),
            required=overrides.get("required", ["summary", "worker_id"]),
            additional_properties=overrides.get("additional_properties", False),
        )

    def test_validate_valid_handoff(self):
        schema = self._make_schema()
        payload = {"summary": "Done", "worker_id": "w01"}
        result = self.verifier.validate(schema, payload, AgentCompletionStatus.COMPLETED)
        assert result.valid
        assert len(result.errors) == 0

    def test_validate_missing_required_field(self):
        schema = self._make_schema()
        payload = {"summary": "Done"}  # missing worker_id
        result = self.verifier.validate(schema, payload, AgentCompletionStatus.COMPLETED)
        assert not result.valid
        error_texts = " ".join(result.errors)
        assert "worker_id" in error_texts

    def test_validate_non_terminal_status(self):
        schema = self._make_schema()
        payload = {"summary": "WIP", "worker_id": "w01"}
        result = self.verifier.validate(schema, payload, AgentCompletionStatus.RUNNING)
        assert not result.valid
        error_texts = " ".join(result.errors)
        assert "terminal" in error_texts or "RUNNING" in error_texts

    def test_validate_type_mismatch(self):
        schema = self._make_schema(properties={
            "count": {"type": "integer"},
        }, required=["count"])
        payload = {"count": "not_a_number"}
        result = self.verifier.validate(schema, payload, AgentCompletionStatus.COMPLETED)
        # Type mismatch is an error
        assert not result.valid

    def test_validate_unknown_field_warning(self):
        schema = self._make_schema(additional_properties=False)
        payload = {"summary": "Done", "worker_id": "w01", "unexpected": "yes"}
        result = self.verifier.validate(schema, payload, AgentCompletionStatus.COMPLETED)
        assert len(result.warnings) > 0
        assert "unexpected" in result.warnings[0]

    def test_validate_unknown_field_with_additional(self):
        schema = self._make_schema(additional_properties=True)
        payload = {"summary": "Done", "worker_id": "w01", "extra": "allowed"}
        result = self.verifier.validate(schema, payload, AgentCompletionStatus.COMPLETED)
        assert result.valid

    def test_validate_enum_field(self):
        schema = self._make_schema(properties={
            "severity": {"type": "string", "enum": ["low", "medium", "high"]},
        }, required=["severity"])
        payload = {"severity": "low"}
        result = self.verifier.validate(schema, payload, AgentCompletionStatus.COMPLETED)
        assert result.valid
        # Invalid enum value
        payload2 = {"severity": "critical"}
        result2 = self.verifier.validate(schema, payload2, AgentCompletionStatus.COMPLETED)
        assert not result2.valid

    def test_validate_status_from_string(self):
        schema = self._make_schema()
        payload = {"summary": "Done", "worker_id": "w01"}
        result = self.verifier.validate(schema, payload, "completed")
        assert result.valid

    def test_validate_status_from_invalid_string(self):
        schema = self._make_schema()
        payload = {"summary": "Done", "worker_id": "w01"}
        result = self.verifier.validate(schema, payload, "bogus_status")
        assert not result.valid

    def test_validate_json_valid(self):
        schema = self._make_schema()
        raw = '{"summary": "Done", "worker_id": "w01"}'
        result = self.verifier.validate_json(schema, raw, AgentCompletionStatus.COMPLETED)
        assert result.valid

    def test_validate_json_invalid(self):
        schema = self._make_schema()
        raw = "not json"
        result = self.verifier.validate_json(schema, raw)
        assert not result.valid
        assert "JSON" in " ".join(result.errors)

    def test_validate_json_non_dict(self):
        schema = self._make_schema()
        raw = '"just a string"'
        result = self.verifier.validate_json(schema, raw)
        assert not result.valid

    def test_terminal_statuses(self):
        statuses = GateVerifier.terminal_statuses()
        assert AgentCompletionStatus.COMPLETED in statuses
        assert AgentCompletionStatus.FAILED in statuses
        assert AgentCompletionStatus.PENDING not in statuses

    def test_validation_result_to_dict(self):
        result = HandoffValidationResult(
            id=1, schema_name="test", valid=True,
            errors=[], warnings=[],
            agent_status=AgentCompletionStatus.COMPLETED,
        )
        d = result.to_dict()
        assert d["valid"] is True
        assert d["agent_status"] == "completed"
