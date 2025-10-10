# RPython tracing overhead

Based on Carl Friedrich Bolz-Tereick's blog post: https://cfbolz.de/posts/speed-of-tracing/

This experiment reproduces the PyPy meta-tracing JIT overhead analysis from Bolz-Tereick's blog post, which demonstrates that the meta-tracing interpreter in PyPy is roughly **900× slower** than CPython on a microbenchmark, though the JIT compilation eventually amortizes this cost for longer-running programs.

## Overview

The benchmark measures PyPy's performance with and without JIT compilation across varying iteration counts to understand:
- The overhead cost of PyPy's meta-tracing interpreter
- The break-even point where JIT compilation becomes beneficial
- The potential speedup achievable after JIT warmup

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

This will install required packages: `matplotlib`, `numpy`, and `click`.

## Files

- `main.py` - CLI tool for running benchmarks and generating plots
- `benchmark.py` - Core benchmark script with 100 replicated test functions (allocation-heavy)
- `benchmarks/` - Directory containing alternative benchmark scripts
  - `fib.py` - Fibonacci benchmark (computation-heavy)
  - `original.py` - Reference copy of the original benchmark
  - `README.md` - Benchmark documentation
- `plot_results.py` - Plotting functions and statistical analysis
- `pyproject.toml` - Project dependencies and configuration
- `README.md` - This file

## Usage

The project provides a command-line interface with several commands. Results are automatically organized into timestamped directories (e.g., `results/2025-10-09_14-30-45/`) so you can run multiple benchmarks and compare them.

### Quick Start

Run the complete benchmark workflow (collect data + generate plots):

```bash
uv run python main.py run
```

This will:
1. Create a timestamped results directory (e.g., `results/2025-10-09_14-30-45/`)
2. Collect data with PyPy (JIT enabled and disabled)
3. Collect CPython baseline data (optional)
4. Generate all plots and statistics in the results directory

**Note**: This process can take significant time (30+ minutes depending on your system).

### Individual Commands

#### 1. Collect benchmark data

```bash
uv run python main.py collect [OPTIONS]
```

**Options:**
- `--start INTEGER` - Starting iteration count (default: 1)
- `--end INTEGER` - Ending iteration count (default: 20000)
- `--step INTEGER` - Step size between iterations (default: 1)
- `--skip-cpython` - Skip CPython baseline collection
- `--collect-jit-logs` - Collect JIT compilation logs using PYPYLOG
- `--force` - Overwrite existing data files without prompting
- `--benchmark-script TEXT` - Path to benchmark script (default: 'benchmark.py')
- `--pypy-path TEXT` - Path to PyPy executable (default: 'pypy')
- `--python-path TEXT` - Path to CPython executable (default: 'python3')
- `--output-dir PATH` - Custom output directory (default: `results/YYYY-MM-DD_HH-MM-SS`)

**Examples:**
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

Creates a timestamped directory under `results/` with data files:
- `data_jit.txt` - PyPy with JIT enabled
- `data_nojit.txt` - PyPy with JIT disabled
- `data_cpython.txt` - CPython baseline (if not skipped)
- `jit_logs/` - JIT compilation logs (if `--collect-jit-logs` enabled)
- `config.json` - Configuration parameters used for this run

#### 2. Generate visualizations

```bash
uv run python main.py plot [OPTIONS]
```

**Options:**
- `--results-dir PATH` - Directory containing benchmark data (default: latest run in `results/`)
- `--output-dir PATH` - Directory to save plots (default: `<results-dir>/plots`)

**Examples:**
```bash
# Plot data from the latest run (automatic)
uv run python main.py plot

# Plot data from a specific run
uv run python main.py plot --results-dir results/2025-10-09_14-30-45

# Save plots to a custom location
uv run python main.py plot --output-dir custom-plots
```

Creates plots in the results directory (or custom location):
- `execution_times.png` - Execution time vs iterations with linear regression fits
- `speedup_factor.png` - JIT speedup over no-JIT
- `overhead_ratio.png` - Overhead ratio compared to CPython
- `cpython_comparison.png` - Direct comparison of JIT vs CPython with fits (requires CPython data)

#### 3. List all benchmark runs

```bash
uv run python main.py list
```

Lists all available benchmark runs with their status and completion information.

**Example output:**
```
Available benchmark runs:

→ 2025-10-09_15-30-22 (latest) - JIT, no-JIT, CPython [plots]
  2025-10-09_14-20-15 - JIT, no-JIT, CPython [plots]
  2025-10-08_10-45-30 - JIT, no-JIT [plots]

Total runs: 3
```

#### 4. Clean up generated files

```bash
uv run python main.py clean [OPTIONS]
```

**Options:**
- `--all` - Remove all benchmark runs (entire `results/` directory)
- `--run-dir PATH` - Remove a specific run directory

**Examples:**
```bash
# Remove only the latest run (default)
uv run python main.py clean

# Remove all benchmark runs
uv run python main.py clean --all

# Remove a specific run
uv run python main.py clean --run-dir results/2025-10-09_14-30-45
```

#### 5. Analyze JIT compilation logs

```bash
uv run python main.py analyze-logs [OPTIONS]
```

Calculates the meta-tracing interpreter slowdown factor (~900×) from JIT compilation logs.
Implements the exact calculation from the blog post.

**Options:**
- `--results-dir PATH` - Results directory containing jit_logs subdirectory [required]
- `--threshold INTEGER` - JIT compilation threshold (default: 1041)

**Examples:**
```bash
# Analyze logs from a specific run
uv run python main.py analyze-logs --results-dir results/2025-10-09_14-30-45

# Use a custom threshold
uv run python main.py analyze-logs --results-dir results/my-run --threshold 2000
```

**Output:**
- Tracing time statistics from JIT logs
- Meta-tracing slowdown factor (how many times slower than regular interpretation)
- Automatically adapts to your data collection step size

**Note:** For accurate results, collect data around iteration 1041:
```bash
uv run python main.py collect --start 1000 --end 1100 --step 1 --collect-jit-logs
```

### Working with Multiple Runs

The CLI automatically organizes results into timestamped directories, making it easy to run multiple benchmarks and compare them:

```bash
# Run first benchmark
uv run python main.py run --end 5000

# Run second benchmark with different parameters
uv run python main.py run --end 10000

# List all runs
uv run python main.py list

# Plot a specific older run
uv run python main.py plot --results-dir results/2025-10-09_14-30-45

# Clean up old runs while keeping the latest
uv run python main.py clean --run-dir results/2025-10-09_14-30-45
```

### CLI Help

View all available commands:

```bash
uv run python main.py --help
```

View help for a specific command:

```bash
uv run python main.py collect --help
uv run python main.py plot --help
uv run python main.py analyze-logs --help
uv run python main.py list --help
uv run python main.py clean --help
```

### Quick Manual Test

To run a single benchmark iteration manually:

```bash
# With JIT (default)
pypy -S benchmark.py 1000

# Without JIT
pypy --jit off -S benchmark.py 1000

# CPython baseline
python3 -S benchmark.py 1000
```

Output format: `<iterations> <elapsed_time_seconds>`

## Expected Results

Based on the original blog post findings:

1. **Meta-tracing overhead**: PyPy without JIT is ~900× slower than CPython at low iteration counts
2. **JIT break-even**: JIT becomes beneficial around ~2,600 iterations
3. **Maximum speedup**: Potential speedup approaches ~200× for this microbenchmark after JIT warmup

Your actual results may vary based on:
- Hardware specifications
- PyPy version
- System load and background processes

## Understanding the Benchmark

The benchmark performs simple operations in a tight loop:
- Object allocation (`A()`)
- Attribute assignment (`a.x = i`)
- Dictionary operations (`d = {"a": a.x}`)
- List operations (`l = [0, 1, d["a"]]`)
- Integer addition (`res += l[-1]`)

These operations are replicated across 100 functions to reduce noise in measurements. The replication helps isolate the JIT compilation overhead by spreading the work across multiple code paths.

## Interpreting Results

### Plot Descriptions

- **Execution Times Plot** (`execution_times.png`): Scatter plot showing execution time vs iterations
  - Color-coded dots: PyPy with JIT (blue), PyPy without JIT (light blue), CPython (green)
  - JIT threshold vertical line at iteration 1041
  - Text box with linear regression statistics and speedup calculations
  - Y-axis in milliseconds for readability

- **Speedup Factor Plot** (`speedup_factor.png`): Shows the ratio of no-JIT to JIT time
  - Values > 1.0 indicate JIT is faster
  - Break-even point shows where JIT compilation pays off

- **Overhead Ratio Plot** (`overhead_ratio.png`): Compares PyPy to CPython baseline
  - Shows meta-tracing interpreter overhead
  - Values > 1.0 indicate PyPy is slower than CPython

- **CPython Comparison Plot** (`cpython_comparison.png`): Direct PyPy JIT vs CPython comparison
  - Shows when PyPy catches up to and surpasses CPython performance
  - Includes regression analysis and intersection calculations

### Color Scheme
- **Blue tones**: PyPy configurations (dark blue = JIT, light blue = no-JIT)
- **Green**: CPython baseline
- **Consistent across all plots** for easy comparison

## References

- Original blog post: https://cfbolz.de/posts/speed-of-tracing/
- PyPy documentation: https://doc.pypy.org/
- PyPy JIT details: https://doc.pypy.org/en/latest/jit/index.html

## License

This experiment is for educational and research purposes, based on publicly available research.


