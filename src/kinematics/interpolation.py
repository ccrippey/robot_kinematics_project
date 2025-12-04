"""Interpolation classes for keyframe animation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import numpy as np


class InterpolationMode(Enum):
    """Interpolation modes for keyframe animation."""

    NONE = "None"
    CONSTANT = "Constant"
    LINEAR = "Linear"
    SINUSOIDAL = "Sinusoidal"
    QUADRATIC = "Quadratic"
    CUBIC = "Cubic"
    ELASTIC = "Elastic"


class InterpolationSpace(Enum):
    """Interpolation space for keyframe animation."""

    JOINT = "Joint"
    CARTESIAN = "Cartesian"


@dataclass
class InterpolationSettings:
    """Settings for interpolation between keyframes."""

    mode: InterpolationMode
    space: InterpolationSpace

    def __init__(self, mode=InterpolationMode.LINEAR, space=InterpolationSpace.JOINT):
        self.mode = mode
        self.space = space


INTERPOLATION_MODES = [mode.value for mode in InterpolationMode if mode != InterpolationMode.NONE]
INTERPOLATION_SPACES = [space.value for space in InterpolationSpace]


class BaseInterpolator(ABC):
    """Abstract base class for interpolators between two parameter values."""

    def __init__(self, t0: float, t1: float, p0: float, p1: float):
        """Initialize interpolator.

        Args:
            t0: Start time
            t1: End time
            p0: Parameter value at t0
            p1: Parameter value at t1
        """
        self.t0 = t0
        self.t1 = t1
        self.p0 = p0
        self.p1 = p1
        self.dt = t1 - t0
        self.dp = p1 - p0

        if self.dt <= 0:
            raise ValueError("End time must be greater than start time")

    @abstractmethod
    def interpolate(self, t: np.ndarray) -> np.ndarray:
        """Compute interpolated parameter values at given times.

        Args:
            t: Array of time values

        Returns:
            Array of interpolated parameter values
        """
        pass

    def _normalize_time(self, t: np.ndarray) -> np.ndarray:
        """Normalize time to [0, 1] range."""
        return np.clip((t - self.t0) / self.dt, 0.0, 1.0)


class ConstantInterpolator(BaseInterpolator):
    """Constant (step) interpolation - holds p0 until switching to p1 at midpoint."""

    def __init__(self, t0: float, t1: float, p0: float, p1: float):
        super().__init__(t0, t1, p0, p1)
        self.t_mid = (t0 + t1) / 2

    def interpolate(self, t: np.ndarray) -> np.ndarray:
        """Step function at midpoint."""
        return np.where(t < self.t_mid, self.p0, self.p1)


class LinearInterpolator(BaseInterpolator):
    """Linear interpolation."""

    def interpolate(self, t: np.ndarray) -> np.ndarray:
        """Linear interpolation: p(t) = p0 + (p1 - p0) * u."""
        u = self._normalize_time(t)
        return self.p0 + self.dp * u


class SinusoidalInterpolator(BaseInterpolator):
    """Sinusoidal (ease-in-out) interpolation."""

    def interpolate(self, t: np.ndarray) -> np.ndarray:
        """Sinusoidal easing: p(u) = p0 + dp * (1 - cos(π*u)) / 2."""
        u = self._normalize_time(t)
        # Smooth S-curve using cosine
        smooth_u = (1 - np.cos(np.pi * u)) / 2
        return self.p0 + self.dp * smooth_u


class QuadraticInterpolator(BaseInterpolator):
    """Quadratic (ease-in-out) interpolation."""

    def interpolate(self, t: np.ndarray) -> np.ndarray:
        """Quadratic easing with smooth acceleration/deceleration."""
        u = self._normalize_time(t)
        # Ease-in for first half, ease-out for second half
        smooth_u = np.where(
            u < 0.5,
            2 * u * u,  # Ease-in: 2u²
            1 - 2 * (1 - u) ** 2,  # Ease-out: 1 - 2(1-u)²
        )
        return self.p0 + self.dp * smooth_u


class CubicInterpolator(BaseInterpolator):
    """Cubic (ease-in-out) interpolation."""

    def interpolate(self, t: np.ndarray) -> np.ndarray:
        """Cubic easing with stronger acceleration/deceleration than quadratic."""
        u = self._normalize_time(t)
        # Ease-in for first half, ease-out for second half
        smooth_u = np.where(
            u < 0.5,
            4 * u * u * u,  # Ease-in: 4u³
            1 - 4 * (1 - u) ** 3,  # Ease-out: 1 - 4(1-u)³
        )
        return self.p0 + self.dp * smooth_u


class ElasticInterpolator(BaseInterpolator):
    """Elastic (spring-like) interpolation with overshoot and oscillation."""

    def __init__(self, t0: float, t1: float, p0: float, p1: float):
        super().__init__(t0, t1, p0, p1)
        # Precompute elastic parameters
        self.amplitude = 1.5  # Overshoot amplitude (must be >= 1)
        self.period = 0.3  # Oscillation period
        self.s = self.period / (2 * np.pi) * np.arcsin(1 / self.amplitude)

    def interpolate(self, t: np.ndarray) -> np.ndarray:
        """Elastic easing with damped oscillation at the end."""
        u = self._normalize_time(t)

        # Elastic ease-out formula
        result = np.ones_like(u) * self.p1

        # Apply elastic effect only where u > 0 and u < 1
        mask = (u > 0) & (u < 1)
        if np.any(mask):
            elastic_u = (
                self.amplitude * np.power(2, -10 * u[mask]) * np.sin((u[mask] - self.s) * (2 * np.pi) / self.period) + 1
            )
            result[mask] = self.p0 + self.dp * elastic_u

        # Handle boundary cases
        result[u <= 0] = self.p0
        result[u >= 1] = self.p1

        return result


# Factory function for creating interpolators
def create_interpolator(mode: str, t0: float, t1: float, p0: float, p1: float) -> BaseInterpolator:
    """Create an interpolator based on the mode string.

    Args:
        mode: Interpolation mode ("Constant", "Linear", etc.)
        t0: Start time
        t1: End time
        p0: Parameter value at t0
        p1: Parameter value at t1

    Returns:
        Appropriate interpolator instance
    """
    interpolators = {
        "Constant": ConstantInterpolator,
        "Linear": LinearInterpolator,
        "Sinusoidal": SinusoidalInterpolator,
        "Quadratic": QuadraticInterpolator,
        "Cubic": CubicInterpolator,
        "Elastic": ElasticInterpolator,
    }

    if mode not in interpolators:
        raise ValueError(f"Unknown interpolation mode: {mode}")

    return interpolators[mode](t0, t1, p0, p1)
