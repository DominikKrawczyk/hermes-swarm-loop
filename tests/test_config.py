"""Tests for Hermes Swarm Loop — config loader.

Covers load_yaml, load_json, load_config, load_scaling_config,
load_yolo_config, merge_configs, and _deep_merge.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.config import (
    DEFAULT_SCALING_CONFIG,
    DEFAULT_YOLO_CONFIG,
    _deep_merge,
    load_config,
    load_json,
    load_scaling_config,
    load_yaml,
    load_yolo_config,
    merge_configs,
)


class TestDeepMerge:
    """_deep_merge recursive merging logic."""

    def test_simple_override(self):
        base = {"a": 1, "b": 2}
        override = {"b": 3}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 3}

    def test_nested_merge(self):
        base = {"outer": {"inner": 1, "keep": 2}}
        override = {"outer": {"inner": 99}}
        result = _deep_merge(base, override)
        assert result["outer"]["inner"] == 99
        assert result["outer"]["keep"] == 2

    def test_new_key_added(self):
        base = {"a": 1}
        override = {"b": 2}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 2}

    def test_empty_override(self):
        base = {"a": 1}
        result = _deep_merge(base, {})
        assert result == {"a": 1}

    def test_empty_base(self):
        override = {"a": 1}
        result = _deep_merge({}, override)
        assert result == {"a": 1}


class TestLoadJson:
    def test_load_valid_json(self, tmp_path: Path):
        p = tmp_path / "test.json"
        p.write_text('{"key": "value"}')
        result = load_json(p)
        assert result == {"key": "value"}

    def test_load_nonexistent(self, tmp_path: Path):
        assert load_json(tmp_path / "nope.json") is None

    def test_load_invalid_json(self, tmp_path: Path):
        p = tmp_path / "bad.json"
        p.write_text("{invalid}")
        assert load_json(p) is None


class TestLoadYaml:
    def test_load_valid_yaml(self, tmp_path: Path):
        p = tmp_path / "test.yaml"
        p.write_text("key: value\nnested:\n  inner: 42\n")
        result = load_yaml(p)
        assert result is not None
        assert result["key"] == "value"
        assert result["nested"]["inner"] == 42

    def test_load_nonexistent(self, tmp_path: Path):
        assert load_yaml(tmp_path / "nope.yaml") is None


class TestLoadConfig:
    def test_load_existing_yaml(self, tmp_path: Path):
        # Point CONFIG_DIR at our tmp by setting env var
        config_dir = tmp_path / "configs"
        config_dir.mkdir()
        (config_dir / "my_config.yaml").write_text("key: 42\n")
        # Monkey-patch via _override
        from engine import config as cfg_mod
        original = cfg_mod.CONFIG_DIR
        try:
            cfg_mod.CONFIG_DIR = config_dir
            result = load_config("my_config", {"key": 0, "default": "yes"})
            assert result["key"] == 42
            assert result["default"] == "yes"
        finally:
            cfg_mod.CONFIG_DIR = original

    def test_falls_back_to_defaults(self, tmp_path: Path):
        from engine import config as cfg_mod
        original = cfg_mod.CONFIG_DIR
        try:
            cfg_mod.CONFIG_DIR = tmp_path / "empty_dir"
            result = load_config("nonexistent", {"fallback": True})
            assert result == {"fallback": True}
        finally:
            cfg_mod.CONFIG_DIR = original

    def test_load_yml_extension(self, tmp_path: Path):
        from engine import config as cfg_mod
        original = cfg_mod.CONFIG_DIR
        try:
            config_dir = tmp_path / "configs"
            config_dir.mkdir()
            (config_dir / "alt.yml").write_text("value: from_yml\n")
            cfg_mod.CONFIG_DIR = config_dir
            result = load_config("alt", {})
            assert result["value"] == "from_yml"
        finally:
            cfg_mod.CONFIG_DIR = original

    def test_load_json_fallback(self, tmp_path: Path):
        from engine import config as cfg_mod
        original = cfg_mod.CONFIG_DIR
        try:
            config_dir = tmp_path / "configs"
            config_dir.mkdir()
            (config_dir / "data.json").write_text('{"score": 99}\n')
            cfg_mod.CONFIG_DIR = config_dir
            result = load_config("data", {"score": 0})
            assert result["score"] == 99
        finally:
            cfg_mod.CONFIG_DIR = original


class TestLoadScalingConfig:
    def test_load_with_defaults(self):
        """load_scaling_config with no args returns merged defaults."""
        config = load_scaling_config()
        assert "agent_scaling" in config
        assert config["agent_scaling"]["default_count"] == 11
        assert "token_bucket" in config
        assert "circuit_breaker" in config
        assert "adaptive_batcher" in config

    def test_load_with_file(self, tmp_path: Path):
        p = tmp_path / "custom_scaling.yaml"
        p.write_text("agent_scaling:\n  default_count: 33\n")
        config = load_scaling_config(str(p))
        assert config["agent_scaling"]["default_count"] == 33
        # Other keys still have defaults
        assert "connection_pool" in config

    def test_load_with_json_file(self, tmp_path: Path):
        p = tmp_path / "custom.json"
        p.write_text('{"token_bucket": {"default_rate": 50.0}}')
        config = load_scaling_config(str(p))
        assert config["token_bucket"]["default_rate"] == 50.0
        assert config["agent_scaling"]["default_count"] == 11


class TestLoadYoloConfig:
    def test_load_with_defaults(self):
        config = load_yolo_config()
        assert "zones" in config
        assert "safe" in config["zones"]
        assert "production" in config["zones"]
        assert config["default_zone"] == "test"

    def test_load_with_file(self, tmp_path: Path):
        p = tmp_path / "custom_yolo.yaml"
        p.write_text("default_zone: production\n")
        config = load_yolo_config(str(p))
        assert config["default_zone"] == "production"
        assert "safe" in config["zones"]

    def test_load_with_json_file(self, tmp_path: Path):
        p = tmp_path / "custom_yolo.json"
        p.write_text('{"zones": {"safe": {"auto_approve": true, "max_parallel": 1}}}')
        config = load_yolo_config(str(p))
        assert config["zones"]["safe"]["auto_approve"] is True
        assert config["default_zone"] == "test"


class TestMergeConfigs:
    def test_merge_configs(self):
        base = {"a": 1, "b": {"c": 2}}
        override = {"b": {"d": 3}}
        result = merge_configs(base, override)
        assert result == {"a": 1, "b": {"c": 2, "d": 3}}

    def test_scaling_defaults_structure(self):
        """Smoke-test that DEFAULT_SCALING_CONFIG has expected keys."""
        assert "agent_scaling" in DEFAULT_SCALING_CONFIG
        assert "token_bucket" in DEFAULT_SCALING_CONFIG
        assert "adaptive_batcher" in DEFAULT_SCALING_CONFIG
        assert "circuit_breaker" in DEFAULT_SCALING_CONFIG
        assert "connection_pool" in DEFAULT_SCALING_CONFIG
        assert "priority_queue" in DEFAULT_SCALING_CONFIG
        assert "queue_pressure" in DEFAULT_SCALING_CONFIG

    def test_yolo_defaults_structure(self):
        """Smoke-test that DEFAULT_YOLO_CONFIG has expected zones."""
        zones = DEFAULT_YOLO_CONFIG["zones"]
        for z in ("safe", "test", "staging", "production"):
            assert z in zones
            assert "auto_approve" in zones[z]
            assert "max_parallel" in zones[z]
