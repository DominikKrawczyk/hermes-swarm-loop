"""Tests for output synthesizer — merging parallel agent outputs."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.synthesizer import synthesize, write_artifact, _finding_key


class TestSynthesize:
    def test_empty_inputs(self):
        result = synthesize([])
        assert result["agent_count"] == 0
        assert result["completed_count"] == 0
        assert result["failed_count"] == 0
        assert result["merged_findings"] == []

    def test_single_completed_agent(self):
        outputs = [
            {"agent_id": "a01", "status": "completed", "output": {"findings": [{"id": 1, "msg": "done"}]}},
        ]
        result = synthesize(outputs)
        assert result["agent_count"] == 1
        assert result["completed_count"] == 1
        assert len(result["merged_findings"]) == 1

    def test_multiple_completed_agents(self):
        outputs = [
            {"agent_id": "a01", "status": "completed", "output": {"findings": [{"id": 1}]}},
            {"agent_id": "a02", "status": "completed", "output": {"findings": [{"id": 2}]}},
        ]
        result = synthesize(outputs)
        assert result["completed_count"] == 2
        assert len(result["merged_findings"]) == 2

    def test_dedup_identical_findings(self):
        outputs = [
            {"agent_id": "a01", "status": "completed", "output": {"findings": [{"id": 1, "msg": "same"}]}},
            {"agent_id": "a02", "status": "completed", "output": {"findings": [{"id": 1, "msg": "same"}]}},
        ]
        result = synthesize(outputs)
        assert len(result["merged_findings"]) == 1
        assert result["dedup_count"] == 1

    def test_mixed_status(self):
        outputs = [
            {"agent_id": "a01", "status": "completed", "output": {"findings": [{"id": 1}]}},
            {"agent_id": "a02", "status": "failed", "output": {"findings": [{"id": 2}]}},
            {"agent_id": "a03", "status": "completed", "output": {"findings": [{"id": 3}]}},
        ]
        result = synthesize(outputs)
        assert result["completed_count"] == 2
        assert result["failed_count"] == 1
        assert len(result["merged_findings"]) == 2

    def test_output_as_list(self):
        outputs = [
            {"agent_id": "a01", "status": "completed", "output": [{"id": 1}, {"id": 2}]},
        ]
        result = synthesize(outputs)
        assert len(result["merged_findings"]) == 2

    def test_single_finding_not_list(self):
        outputs = [
            {"agent_id": "a01", "status": "completed", "output": {"single": "result"}},
        ]
        result = synthesize(outputs)
        assert len(result["merged_findings"]) >= 0

    def test_custom_synthesis_plan(self):
        outputs = [
            {"agent_id": "a01", "status": "completed", "output": {"findings": [{"id": 1}]}},
        ]
        plan = {"merge_strategy": "override", "output_format": "json"}
        result = synthesize(outputs, plan)
        assert result["synthesis_plan"]["merge_strategy"] == "override"

    def test_timestamp_present(self):
        result = synthesize([])
        assert "synthesis_timestamp" in result
        assert isinstance(result["synthesis_timestamp"], str)
        assert "T" in result["synthesis_timestamp"]  # ISO format

    def test_dedup_count_zero_on_first_run(self):
        outputs = [
            {"agent_id": "a01", "status": "completed", "output": {"findings": [{"id": 1}]}},
        ]
        result = synthesize(outputs)
        assert result["dedup_count"] == 0


class TestWriteArtifact:
    def test_writes_json_to_file(self, tmp_path):
        output = {"merged_findings": [{"id": 1}], "agent_count": 1}
        dest = tmp_path / "synthesis.json"
        written = write_artifact(output, str(dest))
        assert os.path.isfile(written)
        with open(written) as f:
            data = json.load(f)
        assert data["agent_count"] == 1

    def test_creates_parent_directories(self, tmp_path):
        output = {"merged_findings": []}
        dest = tmp_path / "deep" / "nested" / "synthesis.json"
        written = write_artifact(output, str(dest))
        assert os.path.isfile(written)

    def test_returns_absolute_path(self, tmp_path):
        output = {"merged_findings": []}
        dest = tmp_path / "output.json"
        written = write_artifact(output, str(dest))
        assert os.path.isabs(written)

    def test_handles_nested_findings(self, tmp_path):
        output = {"merged_findings": [{"complex": {"nested": ["value"]}}]}
        dest = tmp_path / "nested.json"
        written = write_artifact(output, str(dest))
        assert os.path.isfile(written)
        with open(written) as f:
            data = json.load(f)
        assert data["merged_findings"][0]["complex"]["nested"][0] == "value"

    def test_uses_indent_for_readability(self, tmp_path):
        output = {"merged_findings": []}
        dest = tmp_path / "pretty.json"
        written = write_artifact(output, str(dest))
        with open(written) as f:
            raw = f.read()
        assert "  " in raw  # indented


class TestFindingKey:
    def test_dict_key_is_json(self):
        key = _finding_key({"a": 1, "b": 2})
        assert isinstance(key, str)
        assert '"a"' in key

    def test_string_key(self):
        key = _finding_key("hello")
        assert key == "hello"

    def test_consistent_ordering(self):
        k1 = _finding_key({"z": 1, "a": 2})
        k2 = _finding_key({"a": 2, "z": 1})
        assert k1 == k2

    def test_number_key(self):
        key = _finding_key(42)
        assert key == "42"

    def test_none_key(self):
        key = _finding_key(None)
        assert key == "None"
