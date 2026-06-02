"""Tests for Mastery Gate engine — ScoreCard, MasteryGate, score_from_dict.

Matches the current API as built by Phase 1 architecture agents.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.mastery_gate import DIMENSIONS, MasteryGate, ScoreCard, score_from_dict


class TestScoreCard:
    def test_weighted_total_perfect(self):
        sc = ScoreCard(
            correctness=1.0, safety=1.0, test_coverage=1.0,
            consistency=1.0, diversity=1.0, efficiency=1.0, clarity=1.0,
        )
        assert sc.weighted_total == 1.0
        assert sc.verdict == "PASS"

    def test_weighted_total_zero(self):
        sc = ScoreCard()
        assert sc.weighted_total == 0.0
        assert sc.verdict == "BLOCK"

    def test_verdict_pass(self):
        sc = ScoreCard(
            correctness=0.9, safety=0.85, test_coverage=0.8,
            consistency=0.85, diversity=0.75, efficiency=0.8, clarity=0.9,
        )
        assert sc.weighted_total >= 0.70
        assert sc.verdict == "PASS"

    def test_verdict_cross_check(self):
        sc = ScoreCard(
            correctness=0.6, safety=0.65, test_coverage=0.55,
            consistency=0.6, diversity=0.5, efficiency=0.5, clarity=0.6,
        )
        assert 0.50 <= sc.weighted_total < 0.70
        assert sc.verdict == "CROSS-CHECK"

    def test_verdict_review(self):
        sc = ScoreCard(
            correctness=0.4, safety=0.45, test_coverage=0.3,
            consistency=0.4, diversity=0.35, efficiency=0.3, clarity=0.4,
        )
        assert 0.30 <= sc.weighted_total < 0.50
        assert sc.verdict == "REVIEW"

    def test_verdict_block(self):
        sc = ScoreCard(
            correctness=0.1, safety=0.1, test_coverage=0.0,
            consistency=0.1, diversity=0.1, efficiency=0.1, clarity=0.1,
        )
        assert sc.weighted_total < 0.30
        assert sc.verdict == "BLOCK"

    def test_to_dict(self):
        sc = ScoreCard(
            correctness=0.9, safety=0.85, test_coverage=0.8,
            consistency=0.85, diversity=0.75, efficiency=0.8, clarity=0.9,
        )
        d = sc.to_dict()
        assert "scores" in d
        assert "weighted_total" in d
        assert "verdict" in d
        assert "notes" in d
        assert d["verdict"] == "PASS"

    def test_notes_property(self):
        sc = ScoreCard(correctness=0.5, notes={"custom": "review needed"})
        assert sc.notes["custom"] == "review needed"


class TestMasteryGate:
    def test_evaluate_averages_scores(self):
        gate = MasteryGate()
        sc1 = ScoreCard(correctness=0.8, safety=0.8, test_coverage=0.8,
                        consistency=0.8, diversity=0.8, efficiency=0.8, clarity=0.8)
        sc2 = ScoreCard(correctness=1.0, safety=1.0, test_coverage=1.0,
                        consistency=1.0, diversity=1.0, efficiency=1.0, clarity=1.0)
        result = gate.evaluate([sc1, sc2])
        assert isinstance(result, ScoreCard)
        assert result.correctness == 0.9
        assert result.safety == 0.9

    def test_evaluate_single_score(self):
        gate = MasteryGate()
        sc = ScoreCard(correctness=0.9, safety=0.85, test_coverage=0.8,
                       consistency=0.85, diversity=0.75, efficiency=0.8, clarity=0.9)
        result = gate.evaluate([sc])
        assert abs(result.weighted_total - 0.8425) < 0.01
        assert result.verdict == "PASS"

    def test_evaluate_empty_list_raises(self):
        gate = MasteryGate()
        import pytest
        with pytest.raises(ValueError, match="No agent scores"):
            gate.evaluate([])

    def test_check_diversification_passes(self):
        gate = MasteryGate()
        sc = ScoreCard(
            diversity=0.8, correctness=0.9, safety=0.9,
            test_coverage=0.8, consistency=0.8, efficiency=0.8, clarity=0.8,
        )
        gaps = gate.check_diversification(sc)
        assert len(gaps) == 0

    def test_check_diversification_flags_low_diversity(self):
        gate = MasteryGate()
        sc = ScoreCard(diversity=0.3)
        gaps = gate.check_diversification(sc)
        assert any("diversity" in g for g in gaps)

    def test_as_dict_includes_all_keys(self):
        gate = MasteryGate()
        sc = ScoreCard(correctness=0.9, safety=0.85, test_coverage=0.8,
                       consistency=0.85, diversity=0.75, efficiency=0.8, clarity=0.9)
        d = gate.as_dict("development", "architecture", sc,
                         agents_used=3, time_seconds=45.0)
        assert d["phase"] == "development"
        assert d["point"] == "architecture"
        assert d["score"]["verdict"] == "PASS"
        assert d["agents_used"] == 3
        assert d["time_seconds"] == 45.0
        assert "gaps" in d

    def test_default_prd_areas(self):
        gate = MasteryGate()
        assert len(gate.prd_areas) >= 5


class TestScoreFromDict:
    def test_from_partial_dict(self):
        sc = score_from_dict({"correctness": 0.9, "safety": 0.8})
        assert sc.correctness == 0.9
        assert sc.safety == 0.8
        assert sc.test_coverage == 0.0  # default

    def test_from_full_dict(self):
        d = {
            "correctness": 0.9, "safety": 0.8, "test_coverage": 0.85,
            "consistency": 0.8, "diversity": 0.7, "efficiency": 0.75,
            "clarity": 0.9,
        }
        sc = score_from_dict(d)
        assert sc.correctness == 0.9
        assert sc.clarity == 0.9

    def test_from_dict_with_notes(self):
        d = {"correctness": 0.7, "notes": {"dim_a": "missing tests"}}
        sc = score_from_dict(d)
        assert sc.notes["dim_a"] == "missing tests"

    def test_from_empty_dict(self):
        sc = score_from_dict({})
        assert sc.weighted_total == 0.0
        assert sc.verdict == "BLOCK"


class TestDimensions:
    def test_dimensions_sum_to_one(self):
        total = sum(DIMENSIONS.values())
        assert abs(total - 1.0) < 0.001

    def test_dimensions_has_all_seven(self):
        assert set(DIMENSIONS.keys()) == {
            "correctness", "safety", "test_coverage",
            "consistency", "diversity", "efficiency", "clarity",
        }

    def test_correctness_has_highest_weight(self):
        assert DIMENSIONS["correctness"] == max(DIMENSIONS.values())
