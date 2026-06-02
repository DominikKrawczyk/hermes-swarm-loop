"""Configuration loader — loads YAML configs from configs/ directory with fallback."""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Try to import PyYAML; fall back to JSON-only if not available
try:
    import yaml as _yaml  # type: ignore

    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

SWARM_DIR = Path(os.environ.get("HERMES_SWARM_LOOP_DIR", ".")).resolve()
CONFIG_DIR = SWARM_DIR / "configs"

# ─── Default configurations ───

DEFAULT_SCALING_CONFIG: Dict[str, Any] = {
    "agent_scaling": {
        "default_count": 11,
        "yolo_safe": 5,
        "yolo_test": 11,
        "yolo_staging": 33,
        "yolo_production": 999,
        "auto_detect_enabled": True,
    },
    "token_bucket": {"default_rate": 10.0, "default_burst": 50, "backoff_factor": 2.0, "max_retries": 3},
    "adaptive_batcher": {"min_batch_size": 5, "max_batch_size": 50, "batch_window_ms": 100},
    "circuit_breaker": {"failure_threshold": 5, "recovery_timeout_s": 30, "half_open_max_requests": 3},
    "connection_pool": {"min_connections": 2, "max_connections": 20, "max_idle_time_s": 300},
    "priority_queue": {"max_size": 1000, "default_priority": 5},
    "queue_pressure": {"high_watermark": 0.8, "low_watermark": 0.3},
}

DEFAULT_YOLO_CONFIG: Dict[str, Any] = {
    "zones": {
        "safe": {"auto_approve": False, "max_parallel": 5},
        "test": {"auto_approve": True, "max_parallel": 11},
        "staging": {"auto_approve": True, "max_parallel": 33},
        "production": {"auto_approve": True, "max_parallel": 999},
    },
    "default_zone": "test",
}


def load_yaml(path: Path) -> Optional[Dict[str, Any]]:
    """Load a YAML file. Returns None if YAML is not available."""
    if not path.exists():
        return None
    if not _HAS_YAML:
        return None
    with open(path) as f:
        return _yaml.safe_load(f)  # type: ignore


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file. Returns None on failure."""
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def load_config(filename: str, defaults: Dict[str, Any]) -> Dict[str, Any]:
    """Load config from YAML or JSON, falling back to defaults.

    Tries: configs/<filename>.yaml → configs/<filename>.yml → configs/<filename>.json
    """
    stem = Path(filename).stem
    for ext in [".yaml", ".yml", ".json"]:
        path = CONFIG_DIR / f"{stem}{ext}"
        loaded = load_yaml(path) if ext in (".yaml", ".yml") else load_json(path)
        if loaded is not None:
            return _deep_merge(defaults, loaded)
    return defaults


def load_scaling_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load scaling config, merging file over defaults."""
    if path:
        p = Path(path)
        loaded = load_yaml(p) or load_json(p)
        if loaded:
            return _deep_merge(DEFAULT_SCALING_CONFIG, loaded)
    return load_config("scaling_config", DEFAULT_SCALING_CONFIG)


def load_yolo_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load YOLO config, merging file over defaults."""
    if path:
        p = Path(path)
        loaded = load_yaml(p) or load_json(p)
        if loaded:
            return _deep_merge(DEFAULT_YOLO_CONFIG, loaded)
    return load_config("yolo_config", DEFAULT_YOLO_CONFIG)


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two config dicts — override values win."""
    return _deep_merge(base, override)


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursive dict merge."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
