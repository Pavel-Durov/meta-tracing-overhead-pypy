#!/usr/bin/env python3
"""
Analyze PyPy JIT compilation logs

Extracts statistics from PYPYLOG output to understand JIT overhead.
Based on Carl Friedrich Bolz-Tereick's blog post:
https://cfbolz.de/posts/speed-of-tracing/
"""

import os
import re
import sys
import statistics


def parse_jit_log(filepath):
    """Parse a single JIT log file and extract metrics."""
    metrics = {}

    with open(filepath, 'r') as f:
        content = f.read()

    # Extract timing information
    tracing_match = re.search(r'Tracing:\s+(\d+)\s+([\d.]+)', content)
    backend_match = re.search(r'Backend:\s+(\d+)\s+([\d.]+)', content)
    total_match = re.search(r'TOTAL:\s+([\d.]+)', content)

    if tracing_match:
        metrics['tracing_count'] = int(tracing_match.group(1))
        metrics['tracing_time'] = float(tracing_match.group(2))

    if backend_match:
        metrics['backend_count'] = int(backend_match.group(1))
        metrics['backend_time'] = float(backend_match.group(2))

    if total_match:
        metrics['total_jit_time'] = float(total_match.group(1))

    # Extract operation counts
    ops_patterns = {
        'ops': r'ops:\s+(\d+)',
        'recorded_ops': r'recorded ops:\s+(\d+)',
        'opt_ops': r'opt ops:\s+(\d+)',
        'guards': r'guards:\s+(\d+)',
        'opt_guards': r'opt guards:\s+(\d+)',
        'total_loops': r'Total # of loops:\s+(\d+)',
        'total_bridges': r'Total # of bridges:\s+(\d+)',
    }

    for key, pattern in ops_patterns.items():
        match = re.search(pattern, content)
        if match:
            metrics[key] = int(match.group(1))

    return metrics


def analyze_all_logs(log_dir):
    """Analyze all JIT log files in the directory."""
    log_files = sorted([f for f in os.listdir(log_dir) if f.startswith('out')])

    if not log_files:
        print(f"No log files found in {log_dir}")
        return

    all_metrics = []
    for log_file in log_files:
        filepath = os.path.join(log_dir, log_file)
        metrics = parse_jit_log(filepath)
        if metrics:
            all_metrics.append(metrics)

    if not all_metrics:
        print("No valid metrics found in log files")
        return

    # Calculate statistics
    print("="*70)
    print("PyPy JIT Compilation Statistics")
    print("="*70)
    print(f"\nTotal runs analyzed: {len(all_metrics)}")

    # Timing statistics
    if 'tracing_time' in all_metrics[0]:
        tracing_times = [m['tracing_time'] for m in all_metrics]
        backend_times = [m['backend_time'] for m in all_metrics]
        total_times = [m['total_jit_time'] for m in all_metrics]

        print("\nJIT Compilation Time (seconds):")
        print(f"  Tracing:  mean={statistics.mean(tracing_times):.6f}, "
              f"median={statistics.median(tracing_times):.6f}, "
              f"stdev={statistics.stdev(tracing_times):.6f}")
        print(f"  Backend:  mean={statistics.mean(backend_times):.6f}, "
              f"median={statistics.median(backend_times):.6f}, "
              f"stdev={statistics.stdev(backend_times):.6f}")
        print(f"  Total:    mean={statistics.mean(total_times):.6f}, "
              f"median={statistics.median(total_times):.6f}, "
              f"stdev={statistics.stdev(total_times):.6f}")

    # Operation counts
    if 'ops' in all_metrics[0]:
        ops = [m['ops'] for m in all_metrics]
        recorded_ops = [m['recorded_ops'] for m in all_metrics]
        opt_ops = [m['opt_ops'] for m in all_metrics]

        print("\nOperation Counts:")
        print(f"  Total ops:        mean={statistics.mean(ops):.0f}")
        print(f"  Recorded ops:     mean={statistics.mean(recorded_ops):.0f}")
        print(f"  Optimized ops:    mean={statistics.mean(opt_ops):.0f}")
        print(f"  Reduction ratio:  {statistics.mean(opt_ops)/statistics.mean(ops):.2%}")

    # Guard counts
    if 'guards' in all_metrics[0]:
        guards = [m['guards'] for m in all_metrics]
        opt_guards = [m['opt_guards'] for m in all_metrics]

        print("\nGuard Counts:")
        print(f"  Total guards:     mean={statistics.mean(guards):.0f}")
        print(f"  Optimized guards: mean={statistics.mean(opt_guards):.0f}")
        print(f"  Reduction ratio:  {statistics.mean(opt_guards)/statistics.mean(guards):.2%}")

    # Loop/bridge counts
    if 'total_loops' in all_metrics[0]:
        loops = [m['total_loops'] for m in all_metrics]
        bridges = [m['total_bridges'] for m in all_metrics]

        print("\nTrace Structure:")
        print(f"  Total loops:      mean={statistics.mean(loops):.0f}")
        print(f"  Total bridges:    mean={statistics.mean(bridges):.0f}")

    # Tracing count
    if 'tracing_count' in all_metrics[0]:
        tracing_counts = [m['tracing_count'] for m in all_metrics]
        print(f"\nTraces compiled:    mean={statistics.mean(tracing_counts):.0f}")

    print("\n" + "="*70)

    return all_metrics


def main():
    """Main function."""
    log_dir = "results/jit_logs"

    if not os.path.exists(log_dir):
        print(f"Error: {log_dir} directory not found.")
        print("Please run collect_jit_logs.sh first.")
        sys.exit(1)

    analyze_all_logs(log_dir)


if __name__ == "__main__":
    main()
