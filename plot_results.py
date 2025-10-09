#!/usr/bin/env python3
"""
Visualization script for PyPy JIT overhead analysis

Creates plots showing:
1. Execution time vs iterations for JIT and no-JIT configurations
2. Speedup factor between JIT and no-JIT
3. Comparison with CPython baseline (if available)

Based on Carl Friedrich Bolz-Tereick's blog post:
https://cfbolz.de/posts/speed-of-tracing/
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


def load_data(filepath):
    """Load benchmark data from file."""
    if not os.path.exists(filepath):
        return None

    iterations = []
    times = []

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) == 2:
                iterations.append(int(parts[0]))
                times.append(float(parts[1]))

    return np.array(iterations), np.array(times)


def plot_execution_times(data_dict, output_dir):
    """Plot execution times for different configurations."""
    plt.figure(figsize=(12, 8))

    for label, data in data_dict.items():
        if data is not None:
            iterations, times = data
            plt.plot(iterations, times, label=label, marker='o', markersize=2, alpha=0.7)

    plt.xlabel('Number of Iterations', fontsize=12)
    plt.ylabel('Execution Time (seconds)', fontsize=12)
    plt.title('PyPy JIT Overhead: Execution Time vs Iterations', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    output_path = os.path.join(output_dir, 'execution_times.png')
    plt.savefig(output_path, dpi=300)
    print(f"Saved: {output_path}")
    plt.close()


def plot_speedup(jit_data, nojit_data, output_dir):
    """Plot speedup factor between JIT and no-JIT."""
    if jit_data is None or nojit_data is None:
        print("Warning: Cannot plot speedup - missing JIT or no-JIT data")
        return

    jit_iter, jit_times = jit_data
    nojit_iter, nojit_times = nojit_data

    # Create dictionaries for lookup
    jit_dict = dict(zip(jit_iter, jit_times))
    nojit_dict = dict(zip(nojit_iter, nojit_times))

    # Find common iterations
    common_iters = sorted(set(jit_dict.keys()) & set(nojit_dict.keys()))

    # Extract aligned data
    jit_times_aligned = np.array([jit_dict[i] for i in common_iters])
    nojit_times_aligned = np.array([nojit_dict[i] for i in common_iters])
    common_iters = np.array(common_iters)

    # Calculate speedup (no-JIT time / JIT time)
    # Values > 1 mean JIT is faster
    speedup = nojit_times_aligned / jit_times_aligned

    plt.figure(figsize=(12, 8))
    plt.plot(common_iters, speedup, label='Speedup (no-JIT / JIT)',
             marker='o', markersize=2, alpha=0.7, color='green')
    plt.axhline(y=1.0, color='r', linestyle='--', alpha=0.5, label='Break-even (1x)')

    plt.xlabel('Number of Iterations', fontsize=12)
    plt.ylabel('Speedup Factor', fontsize=12)
    plt.title('PyPy JIT Speedup Factor vs Iterations', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    output_path = os.path.join(output_dir, 'speedup_factor.png')
    plt.savefig(output_path, dpi=300)
    print(f"Saved: {output_path}")
    plt.close()


def plot_overhead_ratio(jit_data, nojit_data, cpython_data, output_dir):
    """Plot the overhead ratios comparing meta-tracing to CPython."""
    if cpython_data is None:
        print("Warning: Cannot plot overhead ratio - missing CPython data")
        return

    plt.figure(figsize=(12, 8))

    cp_iter, cp_times = cpython_data
    cp_dict = dict(zip(cp_iter, cp_times))

    if jit_data is not None:
        jit_iter, jit_times = jit_data
        jit_dict = dict(zip(jit_iter, jit_times))

        common_iters = sorted(set(jit_dict.keys()) & set(cp_dict.keys()))
        jit_times_aligned = np.array([jit_dict[i] for i in common_iters])
        cp_times_aligned = np.array([cp_dict[i] for i in common_iters])

        overhead = jit_times_aligned / cp_times_aligned
        plt.plot(common_iters, overhead, label='JIT / CPython',
                marker='o', markersize=2, alpha=0.7)

    if nojit_data is not None:
        nojit_iter, nojit_times = nojit_data
        nojit_dict = dict(zip(nojit_iter, nojit_times))

        common_iters = sorted(set(nojit_dict.keys()) & set(cp_dict.keys()))
        nojit_times_aligned = np.array([nojit_dict[i] for i in common_iters])
        cp_times_aligned = np.array([cp_dict[i] for i in common_iters])

        overhead = nojit_times_aligned / cp_times_aligned
        plt.plot(common_iters, overhead, label='No-JIT / CPython',
                marker='o', markersize=2, alpha=0.7)

    plt.axhline(y=1.0, color='r', linestyle='--', alpha=0.5, label='CPython baseline')
    plt.xlabel('Number of Iterations', fontsize=12)
    plt.ylabel('Overhead Ratio (PyPy / CPython)', fontsize=12)
    plt.title('PyPy Overhead Compared to CPython', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    output_path = os.path.join(output_dir, 'overhead_ratio.png')
    plt.savefig(output_path, dpi=300)
    print(f"Saved: {output_path}")
    plt.close()


def calculate_statistics(data_dict):
    """Calculate and print statistics from the benchmark data."""
    print("\n" + "="*60)
    print("BENCHMARK STATISTICS")
    print("="*60)

    for label, data in data_dict.items():
        if data is not None:
            iterations, times = data
            print(f"\n{label}:")
            print(f"  Total runs: {len(iterations)}")
            print(f"  Iteration range: {iterations.min()} to {iterations.max()}")
            print(f"  Time range: {times.min():.6f}s to {times.max():.6f}s")
            print(f"  Average time: {times.mean():.6f}s")
            print(f"  Median time: {np.median(times):.6f}s")

    # Calculate speedup statistics
    jit_data = data_dict.get('PyPy with JIT')
    nojit_data = data_dict.get('PyPy without JIT')

    if jit_data is not None and nojit_data is not None:
        jit_iter, jit_times = jit_data
        nojit_iter, nojit_times = nojit_data

        jit_dict = dict(zip(jit_iter, jit_times))
        nojit_dict = dict(zip(nojit_iter, nojit_times))

        common_iters = sorted(set(jit_dict.keys()) & set(nojit_dict.keys()))
        jit_times_aligned = np.array([jit_dict[i] for i in common_iters])
        nojit_times_aligned = np.array([nojit_dict[i] for i in common_iters])
        common_iters = np.array(common_iters)

        speedup = nojit_times_aligned / jit_times_aligned

        print(f"\nSpeedup Statistics (no-JIT / JIT):")
        print(f"  Maximum speedup: {speedup.max():.2f}x")
        print(f"  Average speedup: {speedup.mean():.2f}x")
        print(f"  Median speedup: {np.median(speedup):.2f}x")

        # Find break-even point (where JIT becomes faster)
        breakeven_idx = np.where(speedup > 1.0)[0]
        if len(breakeven_idx) > 0:
            breakeven_iter = common_iters[breakeven_idx[0]]
            print(f"  JIT break-even point: ~{breakeven_iter} iterations")

    # Calculate overhead compared to CPython
    cpython_data = data_dict.get('CPython')
    if cpython_data is not None and nojit_data is not None:
        cp_iter, cp_times = cpython_data
        nojit_iter, nojit_times = nojit_data

        cp_dict = dict(zip(cp_iter, cp_times))
        nojit_dict = dict(zip(nojit_iter, nojit_times))

        common_iters = sorted(set(nojit_dict.keys()) & set(cp_dict.keys()))
        nojit_times_aligned = np.array([nojit_dict[i] for i in common_iters])
        cp_times_aligned = np.array([cp_dict[i] for i in common_iters])

        overhead = nojit_times_aligned / cp_times_aligned

        print(f"\nMeta-Tracing Overhead (PyPy no-JIT / CPython):")
        print(f"  Maximum overhead: {overhead.max():.2f}x")
        print(f"  Average overhead: {overhead.mean():.2f}x")
        print(f"  Median overhead: {np.median(overhead):.2f}x")

    print("\n" + "="*60)


def main():
    """Main function to load data and generate plots."""
    results_dir = "results"

    if not os.path.exists(results_dir):
        print(f"Error: {results_dir} directory not found.")
        print("Please run collect_data.sh first to generate benchmark data.")
        sys.exit(1)

    # Load data files
    print("Loading benchmark data...")
    data_dict = {
        'PyPy with JIT': load_data(os.path.join(results_dir, 'data_jit.txt')),
        'PyPy without JIT': load_data(os.path.join(results_dir, 'data_nojit.txt')),
        'CPython': load_data(os.path.join(results_dir, 'data_cpython.txt'))
    }

    # Check if we have any data
    if all(data is None for data in data_dict.values()):
        print("Error: No data files found in results directory.")
        print("Please run collect_data.sh first.")
        sys.exit(1)

    # Create plots directory
    plots_dir = os.path.join(results_dir, 'plots')
    os.makedirs(plots_dir, exist_ok=True)

    print("Generating plots...")

    # Generate plots
    plot_execution_times(data_dict, plots_dir)
    plot_speedup(data_dict['PyPy with JIT'], data_dict['PyPy without JIT'], plots_dir)
    plot_overhead_ratio(data_dict['PyPy with JIT'], data_dict['PyPy without JIT'],
                        data_dict['CPython'], plots_dir)

    # Calculate and display statistics
    calculate_statistics(data_dict)

    print(f"\nAll plots saved to {plots_dir}/")
    print("  - execution_times.png")
    print("  - speedup_factor.png")
    if data_dict['CPython'] is not None:
        print("  - overhead_ratio.png")


if __name__ == "__main__":
    try:
        import matplotlib
        main()
    except ImportError:
        print("Error: matplotlib is required for plotting.")
        print("Install it with: pip install matplotlib numpy")
        sys.exit(1)
