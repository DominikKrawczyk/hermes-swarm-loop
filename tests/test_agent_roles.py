"""Tests for Hermes Swarm Loop — agent role definitions.

Covers AGENT_ROLES dict, total_roles(), get_roles_for_phase(),
_domain_for(), and get_role().
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.agent_roles import AGENT_ROLES, DOMAINS, get_role, get_roles_for_phase, total_roles


class TestAgentRoles:
    def test_total_roles_counts_all(self):
        """total_roles returns exactly 198 (66 + 33 * 4 phases)."""
        n = total_roles()
        assert n == 198  # 66 (prd_build) + 33*4 (development, quality, hunting, simplicity)

    def test_prd_build_has_66_roles(self):
        assert len(AGENT_ROLES["prd_build"]) == 66

    def test_development_has_33_roles(self):
        assert len(AGENT_ROLES["development"]) == 33

    def test_quality_has_33_roles(self):
        assert len(AGENT_ROLES["quality"]) == 33

    def test_hunting_has_33_roles(self):
        assert len(AGENT_ROLES["hunting"]) == 33

    def test_simplicity_has_33_roles(self):
        assert len(AGENT_ROLES["simplicity"]) == 33

    def test_all_phases_present(self):
        for phase in ("prd_build", "development", "hunting", "quality", "simplicity"):
            assert phase in AGENT_ROLES

    def test_get_roles_for_phase(self):
        roles = get_roles_for_phase("development")
        assert len(roles) == 33
        assert roles[0]["kind"] == "architecture"
        assert roles[11]["kind"] == "setup"
        assert roles[22]["kind"] == "code_generation"

    def test_get_roles_for_unknown_phase(self):
        assert get_roles_for_phase("nonexistent") == []

    def test_get_role_found(self):
        role = get_role("architect_01")
        assert role is not None
        assert role["kind"] == "architecture"
        assert role["domain"] in DOMAINS

    def test_get_role_not_found(self):
        assert get_role("ghost_role_99") is None

    def test_prd_build_researchers_are_22(self):
        researchers = [r for r in AGENT_ROLES["prd_build"] if r["kind"] == "research"]
        assert len(researchers) == 22

    def test_prd_build_question_agents_are_22(self):
        question_agents = [r for r in AGENT_ROLES["prd_build"] if r["kind"] == "questions"]
        assert len(question_agents) == 22
        for qa in question_agents:
            assert qa["name"].startswith("prd_question_")

    def test_prd_build_builders_are_22(self):
        builders = [r for r in AGENT_ROLES["prd_build"] if r["kind"] == "build"]
        assert len(builders) == 22

    def test_every_role_has_required_fields(self):
        for phase, roles in AGENT_ROLES.items():
            for role in roles:
                assert "name" in role, f"Missing name in phase {phase}"
                assert "kind" in role, f"Missing kind in {role['name']}"
                assert "domain" in role, f"Missing domain in {role['name']}"
                assert "description" in role, f"Missing description in {role['name']}"

    def test_role_names_are_unique(self):
        names = set()
        for phase, roles in AGENT_ROLES.items():
            for role in roles:
                assert role["name"] not in names, f"Duplicate role name: {role['name']}"
                names.add(role["name"])

    def test_domains_list_has_minimum_entries(self):
        assert len(DOMAINS) >= 20

    def test_domain_for_wraps_around(self):
        from engine.agent_roles import _domain_for
        assert _domain_for(1) == DOMAINS[0]
        assert _domain_for(len(DOMAINS) + 1) == DOMAINS[0]  # wraps around

    def test_get_role_across_phases(self):
        """get_role searches all phases."""
        role = get_role("code_gen_01")
        assert role is not None
        assert role["kind"] == "code_generation"

        role = get_role("security_11")
        assert role is not None
        assert role["kind"] == "security"
