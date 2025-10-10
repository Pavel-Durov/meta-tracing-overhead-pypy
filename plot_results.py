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
    """Plot execution times for different configurations with linear regression fits."""
    THRESHOLD = 1041  # JIT compilation threshold

    plt.figure(figsize=(12, 8))

    jit_data = data_dict.get('PyPy with JIT')
    nojit_data = data_dict.get('PyPy without JIT')

    # Define colors for different configurations - consistent PyPy colors
    colors = {
        'PyPy with JIT': '#1f77b4',      # Blue
        'PyPy without JIT': '#5599ff',   # Light Blue (consistent with PyPy)
        'CPython': '#2ca02c'              # Green
    }

    # Plot scatter points
    for label, data in data_dict.items():
        if data is not None:
            iterations, times = data
            # Convert to milliseconds for better readability
            times_ms = times * 1000
            color = colors.get(label, None)
            plt.scatter(iterations, times_ms, label=label, s=2, alpha=0.5, color=color)


    # Fit lines to JIT and no-JIT data after threshold
    fit_text_lines = []
    intersection_info = None

    if jit_data is not None and nojit_data is not None:
        jit_iter, jit_times = jit_data
        nojit_iter, nojit_times = nojit_data

        # Convert to milliseconds
        jit_times_ms = jit_times * 1000
        nojit_times_ms = nojit_times * 1000

        # Fit JIT data (all data points >= THRESHOLD)
        jit_mask = jit_iter >= THRESHOLD
        if np.any(jit_mask):
            jit_x_fit = jit_iter[jit_mask]
            jit_y_fit = jit_times_ms[jit_mask]

            jit_fit = np.polyfit(jit_x_fit, jit_y_fit, 1)
            # jit_fit_line = np.polyval(jit_fit, jit_iter)
            # plt.plot(jit_iter, jit_fit_line, color='#1f77b4', linestyle='--', linewidth=2, alpha=0.8)
            
            fit_text_lines.append(f'PyPy w/ JIT fit: y = {jit_fit[0]:.6f}x + {jit_fit[1]:.6f}')

        # Fit no-JIT data (all data points >= THRESHOLD)
        nojit_mask = nojit_iter >= THRESHOLD
        if np.any(nojit_mask):
            nojit_x_fit = nojit_iter[nojit_mask]
            nojit_y_fit = nojit_times_ms[nojit_mask]

            nojit_fit = np.polyfit(nojit_x_fit, nojit_y_fit, 1)
            # nojit_fit_line = np.polyval(nojit_fit, nojit_iter)
            # plt.plot(nojit_iter, nojit_fit_line, color='#ff7f0e', linestyle='--', linewidth=2, alpha=0.8)
            
            fit_text_lines.append(f'PyPy w/o JIT fit: y = {nojit_fit[0]:.6f}x + {nojit_fit[1]:.6f}')

            # Calculate intersection and speedup
            if np.any(jit_mask):
                intersection_x = (nojit_fit[1] - jit_fit[1]) / (jit_fit[0] - nojit_fit[0])
                intersection_y = jit_fit[0] * intersection_x + jit_fit[1]
                jit_speedup = 1 / (jit_fit[0] / nojit_fit[0])

                fit_text_lines.append(f'Speedup: {jit_speedup:.2f}x')
                fit_text_lines.append(f'Intersection: ({intersection_x:.2f}, {intersection_y:.2f})')

                # Calculate difference at threshold
                jit_y_at_threshold = jit_fit[0] * THRESHOLD + jit_fit[1]
                nojit_y_at_threshold = nojit_fit[0] * THRESHOLD + nojit_fit[1]
                diff = jit_y_at_threshold - nojit_y_at_threshold
                print(f'Difference at threshold: {diff:.2f} ms')
                intersection_info = (intersection_x, jit_speedup)

    # Add fit parameters text box
    if fit_text_lines:
        fit_text = '\n'.join(fit_text_lines)
        plt.text(0.95, 0.95, fit_text, transform=plt.gca().transAxes, fontsize=10,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'))

    plt.xlabel('Iterations', fontsize=12)
    plt.ylabel('Time taken (milliseconds)', fontsize=12)
    plt.title('Warmup behaviour: PyPy w/ JIT vs PyPy w/o JIT', fontsize=14, fontweight='bold')
    plt.legend(loc='upper left', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    output_path = os.path.join(output_dir, 'execution_times.png')
    plt.savefig(output_path, dpi=300)
    print(f"Saved: {output_path}")
    plt.close()

    return intersection_info


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
             marker='o', markersize=4, linestyle='none', alpha=0.7, color='green')
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


def plot_cpython_comparison(jit_data, cpython_data, output_dir):
    """Plot JIT vs CPython with linear regression fits (blog post style)."""
    if cpython_data is None or jit_data is None:
        print("Warning: Cannot plot CPython comparison - missing data")
        return
    
    THRESHOLD = 1041  # JIT compilation threshold
    
    plt.figure(figsize=(12, 8))
    
    jit_iter, jit_times = jit_data
    cp_iter, cp_times = cpython_data

    # Convert to milliseconds
    jit_times_ms = jit_times * 1000
    cp_times_ms = cp_times * 1000
    
    # Plot scatter points with colors
    plt.scatter(jit_iter, jit_times_ms, label='PyPy w/ JIT', s=2, alpha=0.5, color='#1f77b4')  # Blue (consistent with PyPy)
    plt.scatter(cp_iter, cp_times_ms, label='CPython', s=2, alpha=0.5, color='#2ca02c')  # Green


    # Fit lines after threshold
    fit_text_lines = []

    # Fit JIT data
    jit_mask = jit_iter >= THRESHOLD
    if np.any(jit_mask):
        jit_x_fit = jit_iter[jit_mask]
        jit_y_fit = jit_times_ms[jit_mask]
        
        jit_fit = np.polyfit(jit_x_fit, jit_y_fit, 1)
        # jit_fit_line = np.polyval(jit_fit, jit_iter)
        # plt.plot(jit_iter, jit_fit_line, color='#1f77b4', linestyle='--', linewidth=2, alpha=0.8)
        
        fit_text_lines.append(f'PyPy w/ JIT fit: y = {jit_fit[0]:.6f}x + {jit_fit[1]:.6f}')
    
    # Fit CPython data
    cp_mask = cp_iter >= THRESHOLD
    if np.any(cp_mask):
        cp_x_fit = cp_iter[cp_mask]
        cp_y_fit = cp_times_ms[cp_mask]
        
        cp_fit = np.polyfit(cp_x_fit, cp_y_fit, 1)
        # cp_fit_line = np.polyval(cp_fit, cp_iter)
        # plt.plot(cp_iter, cp_fit_line, color='#2ca02c', linestyle='--', linewidth=2, alpha=0.8)
        
        fit_text_lines.append(f'CPython fit: y = {cp_fit[0]:.6f}x + {cp_fit[1]:.6f}')
        
        # Calculate intersection and speedup
        if np.any(jit_mask):
            intersection_x = (cp_fit[1] - jit_fit[1]) / (jit_fit[0] - cp_fit[0])
            intersection_y = jit_fit[0] * intersection_x + jit_fit[1]
            jit_speedup = 1 / (jit_fit[0] / cp_fit[0])
            
            fit_text_lines.append(f'Speedup: {jit_speedup:.2f}x')
            fit_text_lines.append(f'Intersection: ({intersection_x:.2f}, {intersection_y:.2f})')
    
    # Add fit parameters text box
    if fit_text_lines:
        fit_text = '\n'.join(fit_text_lines)
        plt.text(0.95, 0.95, fit_text, transform=plt.gca().transAxes, fontsize=10,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'))
    
    plt.xlabel('Iterations', fontsize=12)
    plt.ylabel('Time taken (milliseconds)', fontsize=12)
    plt.title('Warmup behaviour: PyPy w/ JIT vs CPython', fontsize=14, fontweight='bold')
    plt.legend(loc='upper left', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    output_path = os.path.join(output_dir, 'cpython_comparison.png')
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
                marker='o', markersize=4, linestyle='none', alpha=0.7)

    if nojit_data is not None:
        nojit_iter, nojit_times = nojit_data
        nojit_dict = dict(zip(nojit_iter, nojit_times))

        common_iters = sorted(set(nojit_dict.keys()) & set(cp_dict.keys()))
        nojit_times_aligned = np.array([nojit_dict[i] for i in common_iters])
        cp_times_aligned = np.array([cp_dict[i] for i in common_iters])

        overhead = nojit_times_aligned / cp_times_aligned
        plt.plot(common_iters, overhead, label='No-JIT / CPython',
                marker='o', markersize=4, linestyle='none', alpha=0.7)

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


def calculate_statistics(data_dict: dict[str, tuple[np.ndarray, np.ndarray]]):
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

        print("\nSpeedup Statistics (no-JIT / JIT):")
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

        print("\nMeta-Tracing Overhead (PyPy no-JIT / CPython):")
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
    data_dict: dict[str, tuple[np.ndarray, np.ndarray]] = {
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
    if data_dict['CPython'] is not None:
        plot_cpython_comparison(data_dict['PyPy with JIT'], data_dict['CPython'], plots_dir)

    # Calculate and display statistics
    calculate_statistics(data_dict)

    print(f"\nAll plots saved to {plots_dir}/")
    print("  - execution_times.png")
    print("  - speedup_factor.png")
    if data_dict['CPython'] is not None:
        print("  - overhead_ratio.png")
        print("  - cpython_comparison.png")
