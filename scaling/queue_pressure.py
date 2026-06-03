"""Queue pressure monitoring and backpressure for Hermes Swarm Loop."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import Enum, auto


class PressureLevel(Enum):
    """Pressure level classifications."""
    LOW = auto()
    MODERATE = auto()
    HIGH = auto()
    CRITICAL = auto()


@dataclass
class PressureMetrics:
    """Simple metrics dataclass."""
    current_depth: int = 0
    avg_depth: float = 0.0
    max_depth: int = 0
    utilisation: float = 0.0
    growth_rate: float = 0.0
    pressure_ratio: float = 0.0
    pressure_level: PressureLevel = PressureLevel.LOW
    sample_count: int = 0
    window_duration: float = 0.0


@dataclass
class Sample:
    """Simple sample dataclass."""
    depth: int = 0
    timestamp: float = 0.0


class QueuePressure:
    """Monitors queue depth and provides backpressure signals.

    A simple, stateless pressure calculator: pressure_ratio = depth / max_depth.
    """

    def __init__(self, max_depth: int = 100):
        if max_depth <= 0:
            raise ValueError(f"max_depth must be > 0, got {max_depth}")
        self.max_depth = max_depth
        self._depth = 0
        self._lock = threading.Lock()

    def record(self, depth: int) -> None:
        """Record the current queue depth.

        Args:
            depth: Current queue depth (must be >= 0).
        """
        if depth < 0:
            raise ValueError(f"depth must be >= 0, got {depth}")
        with self._lock:
            self._depth = depth

    @property
    def pressure_ratio(self) -> float:
        """Pressure ratio as depth / max_depth, clamped to [0.0, 1.0]."""
        with self._lock:
            if self.max_depth <= 0:
                return 0.0
            return min(self._depth / self.max_depth, 1.0)

    @property
    def pressure_level(self) -> PressureLevel:
        """Classify the current pressure ratio into a PressureLevel."""
        r = self.pressure_ratio
        if r < 0.3:
            return PressureLevel.LOW
        elif r < 0.6:
            return PressureLevel.MODERATE
        elif r <= 0.85:
            return PressureLevel.HIGH
        else:
            return PressureLevel.CRITICAL

    def should_throttle(self, threshold: PressureLevel = PressureLevel.HIGH) -> bool:
        """Return True if the pressure level is at or above the given threshold."""
        level_values = {
            PressureLevel.LOW: 0,
            PressureLevel.MODERATE: 1,
            PressureLevel.HIGH: 2,
            PressureLevel.CRITICAL: 3,
        }
        return level_values[self.pressure_level] >= level_values[threshold]

    @property
    def current_depth(self) -> int:
        with self._lock:
            return self._depth

    def reset(self) -> None:
        """Reset the recorded depth to 0."""
        with self._lock:
            self._depth = 0

    def __repr__(self) -> str:
        return (
            f"QueuePressure(depth={self.current_depth}, "
            f"pressure={self.pressure_ratio:.2f}, "
            f"level={self.pressure_level.name})"
        )
