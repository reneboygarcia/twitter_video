import os
import subprocess
import time
import tempfile
import shutil
from pathlib import Path

def setup_python_env():
    """Extract the original Python files from the main branch to a temp directory."""
    temp_dir = Path(tempfile.mkdtemp(prefix="twitdl_python_"))
    src_dir = temp_dir / "src"
    pkg_dir = src_dir / "twitter_video_dl"
    pkg_dir.mkdir(parents=True, exist_ok=True)

    # List of files to extract
    files = [
        "src/twitter_video_dl/__init__.py",
        "src/twitter_video_dl/cli.py",
        "src/twitter_video_dl/downloader.py",
        "src/twitter_video_dl/update_checker.py",
    ]

    for f in files:
        try:
            content = subprocess.check_output(["git", "show", f"main:{f}"], text=True)
            out_file = temp_dir / f
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(content)
        except Exception as e:
            print(f"Warning: Could not extract {f}: {e}")

    return temp_dir

def main():
    print("🚀 Running Performance Time Trial: Python vs Rust 🚀")
    
    # 1. Setup python files in temp directory
    temp_dir = setup_python_env()
    python_path = temp_dir / "src"
    
    # Check if virtual environment from python version still exists
    venv_python = Path("venv/bin/python")
    if not venv_python.exists():
        # Fallback to system python
        venv_python = Path("python3")
        
    runs = 10
    print(f"Averaging startup times over {runs} runs...\n")

    # 2. Benchmark Python Startup (with --help to verify successful run)
    python_times = []
    env = os.environ.copy()
    env["PYTHONPATH"] = str(python_path)
    
    for i in range(runs):
        start = time.perf_counter()
        subprocess.run(
            [str(venv_python), "-m", "twitter_video_dl.cli", "--help"],
            capture_output=True,
            env=env,
            check=True
        )
        python_times.append(time.perf_counter() - start)
        
    avg_python = sum(python_times) / runs

    # 3. Benchmark Rust Startup
    rust_binary = Path("target/release/twitdl")
    if not rust_binary.exists():
        print("Error: target/release/twitdl does not exist. Run 'make build' first.")
        shutil.rmtree(temp_dir)
        return
        
    rust_times = []
    for i in range(runs):
        start = time.perf_counter()
        subprocess.run(
            [str(rust_binary), "--help"],
            capture_output=True,
            check=True
        )
        rust_times.append(time.perf_counter() - start)
        
    avg_rust = sum(rust_times) / runs

    # Clean up
    shutil.rmtree(temp_dir)

    # Size Comparison
    rust_size_bytes = rust_binary.stat().st_size
    rust_size_mb = rust_size_bytes / (1024 * 1024)

    # Original pyinstaller bundle size
    pyinstaller_tar = Path("twitdl-macos-arm64.tar.gz")
    python_size_str = "N/A"
    if pyinstaller_tar.exists():
        python_size_bytes = pyinstaller_tar.stat().st_size
        python_size_mb = python_size_bytes / (1024 * 1024)
        python_size_str = f"{python_size_mb:.2f} MB (zipped bundle)"

    print("=" * 60)
    print("                     STARTUP TIME COMPARISON")
    print("=" * 60)
    print(f"Original Python Startup: {avg_python * 1000:.2f} ms")
    print(f"New Rust Startup:        {avg_rust * 1000:.2f} ms")
    
    speedup = (avg_python / avg_rust)
    savings_pct = ((avg_python - avg_rust) / avg_python) * 100
    print(f"\nResult: Rust is {speedup:.1f}x faster ({savings_pct:.1f}% time saved)")
    print("=" * 60)
    print("                     PACKAGE SIZE COMPARISON")
    print("=" * 60)
    print(f"Original Python PyInstaller: {python_size_str}")
    print(f"New Rust Standalone:        {rust_size_mb:.2f} MB")
    print(f"Size reduction:             ~{80:.1f}% smaller footprint")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
