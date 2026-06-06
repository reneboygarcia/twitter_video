import os
import subprocess
import time
from pathlib import Path

import pytest

binary_exists = Path("dist/twitdl/twitdl").exists()
pytestmark = pytest.mark.skipif(
    not binary_exists,
    reason=(
        "Standalone binary not found at ./dist/twitdl/twitdl. "
        "Run 'make build-bin' first."
    ),
)


def test_binary_existence_and_size():
    """Verify that the binary folder exists and measure its total size."""
    bin_dir = Path("dist/twitdl")
    binary_path = bin_dir / "twitdl"
    assert binary_path.exists(), (
        "Standalone binary not found at ./dist/twitdl/twitdl! "
        "Run 'make build-bin' first."
    )

    # Calculate folder size
    size_bytes = sum(f.stat().st_size for f in bin_dir.rglob("*") if f.is_file())
    size_mb = size_bytes / (1024 * 1024)
    print(f"\n📦 Standalone Bundle Size: {size_mb:.2f} MB ({size_bytes:,} bytes)")
    assert (
        size_mb > 5.0
    ), "Bundle size is unexpectedly small. Packaging might have failed."


def test_binary_execution():
    """Verify that the standalone binary runs correctly and displays help output."""
    binary_path = Path("dist/twitdl/twitdl")
    assert binary_path.exists()

    # Run the binary with --help
    result = subprocess.run(
        [str(binary_path), "--help"], capture_output=True, text=True, check=True
    )

    # Assert correct execution
    assert result.returncode == 0
    assert "Usage: twitdl" in result.stdout or "twitdl" in result.stdout.lower()
    assert "--quality" in result.stdout
    assert "--output" in result.stdout


def test_binary_performance_time_trial():
    """Run a time trial benchmark comparing python startup vs binary startup."""
    binary_path = Path("dist/twitdl/twitdl")
    assert binary_path.exists()

    runs = 5
    print(f"\n⏱️ Starting performance time trial ({runs} runs averaged)...")

    # 1. Benchmark python virtualenv execution
    python_times = []
    for i in range(runs):
        start = time.perf_counter()
        subprocess.run(
            ["venv/bin/python", "-m", "twitter_video_dl.cli", "--help"],
            capture_output=True,
            check=True,
            env={**os.environ, "PYTHONPATH": "src"},
        )
        python_times.append(time.perf_counter() - start)

    avg_python = sum(python_times) / runs

    # 2. Benchmark standalone binary execution
    binary_times = []
    for i in range(runs):
        start = time.perf_counter()
        subprocess.run([str(binary_path), "--help"], capture_output=True, check=True)
        binary_times.append(time.perf_counter() - start)

    avg_binary = sum(binary_times) / runs

    # Calculate difference
    diff_pct = ((avg_binary - avg_python) / avg_python) * 100

    print("\n" + "=" * 50)
    print("🚀 PERFORMANCE TIME TRIAL RESULTS 🚀")
    print("=" * 50)
    print(f"Python Virtualenv startup: {avg_python * 1000:.2f} ms")
    print(f"Packaged Binary startup:   {avg_binary * 1000:.2f} ms")
    if avg_binary < avg_python:
        savings = ((avg_python - avg_binary) / avg_python) * 100
        print(
            f"Result: Standalone binary is {savings:.1f}% FASTER than Python startup!"
        )
    else:
        print(
            f"Result: Standalone binary is {diff_pct:.1f}% slower "
            "(typical PyInstaller unpacking overhead)"
        )

    print("=" * 50 + "\n")
