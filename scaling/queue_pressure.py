"""Queue pressure monitoring and backpressure for Hermes Swarm Loop."""

from __future__ import annotations

from enum import Enum, auto


class PressureLevel(Enum):
    """Pressure level classifications."""
    LOW = auto()
    MODERATE = auto()
    HIGH = auto()
    CRITICAL = auto()


class PressureMetrics:
    """Simple metrics dataclass for backward compatibility."""

    def __init__(
        self,
        current_depth: int = 0,
        avg_depth: float = 0.0,
        max_depth: int = 0,
        utilisation: float = 0.0,
        growth_rate: float = 0.0,
        pressure_ratio: float = 0.0,
        pressure_level: PressureLevel = PressureLevel.LOW,
        sample_count: int = 0,
        window_duration: float = 0.0,
    ):
        self.current_depth = current_depth
        self.avg_depth = avg_depth
        self.max_depth = max_depth
        self.utilisation = utilisation
        self.growth_rate = growth_rate
        self.pressure_ratio = pressure_ratio
        self.pressure_level = pressure_level
        self.sample_count = sample_count
        self.window_duration = window_duration


class Sample:
    """Simple sample dataclass for backward compatibility."""

    def __init__(self, depth: int, timestamp: float = 0.0):
        self.depth = depth
        self.timestamp = timestamp

    def __repr__(self):
        return f"Sample(depth={self.depth}, ts={self.timestamp:.3f})"


class QueuePressure:
    """Monitors queue depth and provides backpressure signals.

    A simple, stateless pressure calculator: pressure_ratio = depth / max_depth.
    """

    def __init__(self, max_depth: int = 100):
        if max_depth <= 0:
            raise ValueError(f"max_depth must be > 0, got {max_depth}")
        self.max_depth = max_depth
        self._depth = 0

    def record(self, depth: int) -> None:
        """Record the current queue depth.

        Args:
            depth: Current queue depth (must be >= 0).
        """
        if depth < 0:
            raise ValueError(f"depth must be >= 0, got {depth}")
        self._depth = depth

    @property
    def pressure_ratio(self) -> float:
        """Pressure ratio as depth / max_depth, clamped to [0.0, 1.0]."""
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
        return self._depth

    def reset(self) -> None:
        """Reset the recorded depth to 0."""
        self._depth = 0

    def __repr__(self) -> str:
        return (
            f"QueuePressure(depth={self._depth}, "
            f"pressure={self.pressure_ratio:.2f}, "
            f"level={self.pressure_level.name})"
        )
