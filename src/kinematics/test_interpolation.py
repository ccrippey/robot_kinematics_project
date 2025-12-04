#!/usr/bin/env python
"""Test script for interpolation methods."""

import click
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple

from interpolation import InterpolationMode, create_interpolator


# All available interpolation modes
ALL_MODES = [mode.value for mode in InterpolationMode if mode != InterpolationMode.NONE]


def generate_test_cases(n: int = 3, seed: int = 42) -> List[Tuple[float, float, float, float]]:
    """Generate random test cases for interpolation.

    Args:
        n: Number of test cases to generate
        seed: Random seed for reproducibility

    Returns:
        List of (t0, t1, p0, p1) tuples
    """
    rng = np.random.RandomState(seed)

    cases = []
    for _ in range(n):
        t0 = rng.uniform(0, 5)
        t1 = t0 + rng.uniform(1, 5)
        p0 = rng.uniform(-10, 10)
        p1 = rng.uniform(-10, 10)
        cases.append((t0, t1, p0, p1))

    return cases


def generate_sample_times(t0: float, t1: float, n_samples: int = 100, seed: int = 42) -> np.ndarray:
    """Generate random sample times within [t0, t1].

    Args:
        t0: Start time
        t1: End time
        n_samples: Number of samples
        seed: Random seed

    Returns:
        Sorted array of sample times
    """
    rng = np.random.RandomState(seed)
    times = rng.uniform(t0, t1, n_samples)
    return np.sort(times)


def test_interpolator(mode: str, test_cases: List[Tuple[float, float, float, float]]) -> dict:
    """Test a single interpolator mode.

    Args:
        mode: Interpolation mode name
        test_cases: List of (t0, t1, p0, p1) tuples

    Returns:
        Dictionary with test results
    """
    results = {
        "mode": mode,
        "passed": True,
        "issues": [],
    }

    for i, (t0, t1, p0, p1) in enumerate(test_cases):
        interpolator = create_interpolator(mode, t0, t1, p0, p1)
        times = generate_sample_times(t0, t1, 100, seed=42 + i)
        values = interpolator.interpolate(times)

        # Test 1: Check start and end values
        start_val = interpolator.interpolate(np.array([t0]))
        end_val = interpolator.interpolate(np.array([t1]))

        if not np.isclose(start_val, p0, atol=1e-6):
            results["passed"] = False
            results["issues"].append(f"Case {i}: Start value {start_val:.6f} != {p0:.6f}")

        if not np.isclose(end_val, p1, atol=1e-6):
            results["passed"] = False
            results["issues"].append(f"Case {i}: End value {end_val:.6f} != {p1:.6f}")

        # Test 2: Check range (except for Elastic which can overshoot)
        if mode != "Elastic":
            min_val, max_val = (p0, p1) if p0 < p1 else (p1, p0)
            if np.any(values < min_val - 1e-6) or np.any(values > max_val + 1e-6):
                results["passed"] = False
                out_of_range = np.sum((values < min_val - 1e-6) | (values > max_val + 1e-6))
                results["issues"].append(
                    f"Case {i}: {out_of_range}/{len(values)} values outside [{min_val:.3f}, {max_val:.3f}]"
                )

        # Test 3: Check continuity (no dramatic jumps) - skip for Constant mode
        if len(values) > 1 and mode != "Constant":
            diffs = np.abs(np.diff(values))
            max_expected_jump = None

            # For Elastic, allow larger jumps due to oscillation
            if mode == "Elastic":
                max_expected_jump = (
                    np.abs(p1 - p0) * 0.8
                )  # Allow up to 80% of total range per step... which makes this test kinda useless
            else:
                max_expected_jump = np.abs(p1 - p0) * 0.1  # Allow up to 5% of total range per step

            if np.any(diffs > max_expected_jump):
                results["passed"] = False
                max_jump = np.max(diffs)
                results["issues"].append(f"Case {i}: Large discontinuity detected (max jump: {max_jump:.3f})")

        # Test 4: Check for NaN or Inf
        if np.any(~np.isfinite(values)):
            results["passed"] = False
            results["issues"].append(f"Case {i}: Non-finite values detected (NaN or Inf)")

    return results


@click.group()
def cli():
    """Test interpolation methods."""
    pass


@cli.command()
@click.option(
    "--modes",
    "-m",
    multiple=True,
    type=click.Choice(ALL_MODES, case_sensitive=False),
    help="Interpolation modes to test (default: all)",
)
@click.option(
    "--cases",
    "-n",
    default=3,
    help="Number of test cases to generate",
)
def test(modes: Tuple[str, ...], cases: int):
    """Run automated tests on interpolation methods."""
    modes = modes or ALL_MODES
    test_cases = generate_test_cases(cases)

    click.echo(f"\nTesting {len(modes)} interpolation mode(s) with {cases} test case(s) each...\n")
    click.echo("=" * 70)

    all_passed = True
    for mode in modes:
        click.echo(f"\n{mode} Interpolator:")
        click.echo("-" * 70)

        result = test_interpolator(mode, test_cases)

        if result["passed"]:
            click.echo(click.style("✓ PASSED", fg="green", bold=True))
        else:
            click.echo(click.style("✗ FAILED", fg="red", bold=True))
            all_passed = False

            for issue in result["issues"]:
                click.echo(f"  - {issue}")

    click.echo("\n" + "=" * 70)
    if all_passed:
        click.echo(click.style("\n✓ All tests passed!", fg="green", bold=True))
    else:
        click.echo(click.style("\n✗ Some tests failed!", fg="red", bold=True))


@cli.command()
@click.option(
    "--modes",
    "-m",
    multiple=True,
    type=click.Choice(ALL_MODES, case_sensitive=False),
    help="Interpolation modes to display (default: Linear)",
)
@click.option(
    "--samples",
    "-s",
    default=100,
    help="Number of sample points",
)
def display(modes: Tuple[str, ...], samples: int):
    """Display interpolation curves using matplotlib."""
    modes = modes or ("Linear",)

    if len(modes) == 1:
        # Single interpolator: show 3 different test cases
        mode = modes[0]
        test_cases = generate_test_cases(3)

        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        fig.suptitle(f"{mode} Interpolation - 3 Test Cases", fontsize=14, fontweight="bold")

        for i, (ax, (t0, t1, p0, p1)) in enumerate(zip(axes, test_cases)):
            interpolator = create_interpolator(mode, t0, t1, p0, p1)
            times = generate_sample_times(t0, t1, samples, seed=42 + i)
            values = interpolator.interpolate(times)

            ax.plot(times, values, "b-", linewidth=2, label="Interpolated")
            ax.plot([t0, t1], [p0, p1], "ro", markersize=8, label="Keyframes")
            ax.axhline(y=p0, color="r", linestyle="--", alpha=0.3)
            ax.axhline(y=p1, color="r", linestyle="--", alpha=0.3)
            ax.grid(True, alpha=0.3)
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Parameter Value")
            ax.set_title(f"Case {i + 1}: p({t0:.2f}) = {p0:.2f}, p({t1:.2f}) = {p1:.2f}")
            ax.legend()

    else:
        # Multiple interpolators: show same test case with different colors
        t0, t1, p0, p1 = generate_test_cases(1)[0]

        fig, ax = plt.subplots(figsize=(12, 6))
        fig.suptitle(
            f"Comparison of {len(modes)} Interpolation Modes",
            fontsize=14,
            fontweight="bold",
        )

        colors = plt.cm.tab10(np.linspace(0, 1, len(modes)))

        for mode, color in zip(modes, colors):
            interpolator = create_interpolator(mode, t0, t1, p0, p1)
            times = generate_sample_times(t0, t1, samples, seed=42)
            values = interpolator.interpolate(times)

            ax.plot(times, values, linewidth=2, label=mode, color=color)

        ax.plot([t0, t1], [p0, p1], "ko", markersize=10, label="Keyframes", zorder=10)
        ax.axhline(y=p0, color="k", linestyle="--", alpha=0.3)
        ax.axhline(y=p1, color="k", linestyle="--", alpha=0.3)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Parameter Value")
        ax.set_title(f"Test Case: p({t0:.2f}) = {p0:.2f}, p({t1:.2f}) = {p1:.2f}")
        ax.legend(loc="best")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    cli()
