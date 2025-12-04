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
    """Abstract base class for interpolators between two parameter values.

    Supports vectorized interpolation: both p0/p1 can be arrays, and t can be an array.
    Returns shape (len(t), len(p0)) if p0 is array, or (len(t),) if p0 is scalar.
    """

    def __init__(self, t0: float, t1: float, p0, p1):
        """Initialize interpolator.

        Args:
            t0: Start time
            t1: End time
            p0: Parameter value(s) at t0 - scalar or numpy array
            p1: Parameter value(s) at t1 - scalar or numpy array
        """
        self.t0 = t0
        self.t1 = t1
        self.p0 = np.atleast_1d(p0)
        self.p1 = np.atleast_1d(p1)
        self.dt = t1 - t0
        self.dp = self.p1 - self.p0
        self.is_scalar = np.isscalar(p0)

        if self.dt <= 0:
            raise ValueError("End time must be greater than start time")
        if self.p0.shape != self.p1.shape:
            raise ValueError("p0 and p1 must have the same shape")

    @abstractmethod
    def interpolate(self, t: np.ndarray) -> np.ndarray:
        """Compute interpolated parameter values at given times.

        Args:
            t: Array of time values (shape: (n,))

        Returns:
            Array of interpolated parameter values
            - If p0 is scalar: shape (n,)
            - If p0 is array: shape (n, p) where p is number of parameters
        """
        pass

    def _normalize_time(self, t: np.ndarray) -> np.ndarray:
        """Normalize time to [0, 1] range. Returns shape (n,)."""
        return np.clip((t - self.t0) / self.dt, 0.0, 1.0)


class ConstantInterpolator(BaseInterpolator):
    """Constant (step) interpolation - holds p0 until switching to p1 at midpoint."""

    def __init__(self, t0: float, t1: float, p0, p1):
        super().__init__(t0, t1, p0, p1)
        self.t_mid = (t0 + t1) / 2

    def interpolate(self, t: np.ndarray) -> np.ndarray:
        """Step function at midpoint."""
        t = np.atleast_1d(t)
        # Shape: (n, 1) for broadcasting with p0/p1 shape (p,)
        mask = (t < self.t_mid)[:, np.newaxis] if len(self.p0) > 1 else (t < self.t_mid)
        result = np.where(mask, self.p0, self.p1)
        return result[0] if self.is_scalar and len(t) == 1 else result


class LinearInterpolator(BaseInterpolator):
    """Linear interpolation."""

    def interpolate(self, t: np.ndarray) -> np.ndarray:
        """Linear interpolation: p(t) = p0 + (p1 - p0) * u."""
        t = np.atleast_1d(t)
        u = self._normalize_time(t)  # Shape: (n,)
        # Broadcast: u[:, np.newaxis] gives shape (n, 1) for (n, p) output
        if len(self.p0) > 1:
            result = self.p0 + self.dp * u[:, np.newaxis]
        else:
            result = self.p0 + self.dp * u
        return result[0] if self.is_scalar and len(t) == 1 else result


class SinusoidalInterpolator(BaseInterpolator):
    """Sinusoidal (ease-in-out) interpolation."""

    def interpolate(self, t: np.ndarray) -> np.ndarray:
        """Sinusoidal easing: p(u) = p0 + dp * (1 - cos(π*u)) / 2."""
        t = np.atleast_1d(t)
        u = self._normalize_time(t)
        smooth_u = (1 - np.cos(np.pi * u)) / 2
        if len(self.p0) > 1:
            result = self.p0 + self.dp * smooth_u[:, np.newaxis]
        else:
            result = self.p0 + self.dp * smooth_u
        return result[0] if self.is_scalar and len(t) == 1 else result


class QuadraticInterpolator(BaseInterpolator):
    """Quadratic (ease-in-out) interpolation."""

    def interpolate(self, t: np.ndarray) -> np.ndarray:
        """Quadratic easing with smooth acceleration/deceleration."""
        t = np.atleast_1d(t)
        u = self._normalize_time(t)
        smooth_u = np.where(
            u < 0.5,
            2 * u * u,
            1 - 2 * (1 - u) ** 2,
        )
        if len(self.p0) > 1:
            result = self.p0 + self.dp * smooth_u[:, np.newaxis]
        else:
            result = self.p0 + self.dp * smooth_u
        return result[0] if self.is_scalar and len(t) == 1 else result


class CubicInterpolator(BaseInterpolator):
    """Cubic (ease-in-out) interpolation."""

    def interpolate(self, t: np.ndarray) -> np.ndarray:
        """Cubic easing with stronger acceleration/deceleration than quadratic."""
        t = np.atleast_1d(t)
        u = self._normalize_time(t)
        smooth_u = np.where(
            u < 0.5,
            4 * u * u * u,
            1 - 4 * (1 - u) ** 3,
        )
        if len(self.p0) > 1:
            result = self.p0 + self.dp * smooth_u[:, np.newaxis]
        else:
            result = self.p0 + self.dp * smooth_u
        return result[0] if self.is_scalar and len(t) == 1 else result


class ElasticInterpolator(BaseInterpolator):
    """Elastic (spring-like) interpolation with overshoot and oscillation."""

    def __init__(self, t0: float, t1: float, p0, p1):
        super().__init__(t0, t1, p0, p1)
        self.amplitude = 1.5
        self.period = 0.3
        self.s = self.period / (2 * np.pi) * np.arcsin(1 / self.amplitude)

    def interpolate(self, t: np.ndarray) -> np.ndarray:
        """Elastic easing with damped oscillation at the end."""
        t = np.atleast_1d(t)
        u = self._normalize_time(t)

        # Compute elastic_u for all time values
        elastic_u = np.ones_like(u)
        mask = (u > 0) & (u < 1)
        if np.any(mask):
            elastic_u[mask] = (
                self.amplitude * np.power(2, -10 * u[mask]) * np.sin((u[mask] - self.s) * (2 * np.pi) / self.period) + 1
            )
        elastic_u[u <= 0] = 0.0
        elastic_u[u >= 1] = 1.0

        if len(self.p0) > 1:
            result = self.p0 + self.dp * elastic_u[:, np.newaxis]
        else:
            result = self.p0 + self.dp * elastic_u
        return result[0] if self.is_scalar and len(t) == 1 else result


# Factory function for creating interpolators
def create_interpolator(mode: str, t0: float, t1: float, p0, p1) -> BaseInterpolator:
    """Create an interpolator based on the mode string.

    Args:
        mode: Interpolation mode ("Constant", "Linear", etc.)
        t0: Start time
        t1: End time
        p0: Parameter value(s) at t0 - scalar or numpy array
        p1: Parameter value(s) at t1 - scalar or numpy array

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
