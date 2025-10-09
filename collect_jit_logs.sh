#!/bin/bash

# Collect JIT compilation logs using PYPYLOG
# Based on Carl Friedrich Bolz-Tereick's blog post:
# https://cfbolz.de/posts/speed-of-tracing/

set -e

SCRIPT="benchmark.py"
ITERATIONS=1041  # Specific iteration count from blog post
RUNS=100

# Check if PyPy is installed
if ! command -v pypy3 &> /dev/null; then
    echo "Error: PyPy is not installed. Please install PyPy first."
    exit 1
fi

echo "Collecting JIT logs with PYPYLOG..."
echo "Running $RUNS iterations at $ITERATIONS per run..."

# Create logs directory
mkdir -p results/jit_logs

# Clear previous results
rm -f results/jit_times.txt

# Run benchmark multiple times with JIT logging
for i in $(seq 0 1 100); do
    if [ $((i % 10)) -eq 0 ]; then
        echo "Progress: $i / $RUNS runs"
    fi

    # Run with JIT logging - output log to file and time to results
    PYPYLOG=jit-summary:results/jit_logs/out$i pypy3 -S "$SCRIPT" $ITERATIONS >> results/jit_times.txt
done

echo ""
echo "JIT log collection complete!"
echo "Results saved in:"
echo "  - results/jit_times.txt (execution times)"
echo "  - results/jit_logs/out* (JIT compilation logs)"
echo ""
echo "To analyze a specific log file:"
echo "  cat results/jit_logs/out0"
