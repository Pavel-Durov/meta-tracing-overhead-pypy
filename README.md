# RPython tracing overhead

Based on Carl Friedrich Bolz-Tereick's blog post: https://cfbolz.de/posts/speed-of-tracing/

This experiment reproduces the PyPy meta-tracing JIT overhead analysis from Bolz-Tereick's blog post, which demonstrates that the meta-tracing interpreter in PyPy is roughly **900× slower** than CPython on a microbenchmark, though the JIT compilation eventually amortizes this cost for longer-running programs.

## Requirements

- **PyPy** (tested with PyPy 7.3+)
  - Install from: https://www.pypy.org/download.html
  - Or via package manager: `brew install pypy` (macOS) or `apt-get install pypy` (Linux)
- **Python 3.12+** (for the CLI, plotting, and comparison baseline)
- **uv** (recommended package manager)
  - Install from: https://docs.astral.sh/uv/

## Installation

Install dependencies using uv:

```bash
uv sync
```

## Usage

The project provides a command-line interface with several commands. Results are automatically organized into timestamped directories (e.g., `results/2025-10-09_14-30-45/`) so you can run multiple benchmarks and compare them.

### Examples

```bash
# Quick test with fewer iterations
uv run python main.py collect --start 1 --end 5000 --step 10

# Skip CPython baseline
uv run python main.py collect --skip-cpython

# Collect JIT logs for slowdown analysis
uv run python main.py collect --collect-jit-logs

# Use a different benchmark script
uv run python main.py collect --benchmark-script benchmarks/fib.py

# Force overwrite existing data
uv run python main.py collect --force

# Specify custom output directory
uv run python main.py collect --output-dir results/my-custom-run

# Collect data around iteration 1041 for slowdown calculation
uv run python main.py collect --start 1000 --end 1100 --step 1 --collect-jit-logs
```
