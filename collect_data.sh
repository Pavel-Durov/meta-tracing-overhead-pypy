



#!/bin/bash

# Data collection script for PyPy JIT overhead measurement
# Based on Carl Friedrich Bolz-Tereick's blog post:
# https://cfbolz.de/posts/speed-of-tracing/

set -e

# Configuration
SCRIPT="benchmark.py"
START=1
END=20000
STEP=1

# Check if PyPy is installed
if ! command -v pypy &> /dev/null; then
    echo "Error: PyPy is not installed. Please install PyPy first."
    echo "Visit: https://www.pypy.org/download.html"
    exit 1
fi

echo "PyPy version:"
pypy --version
echo ""

# Create results directory
mkdir -p results

# Collect data with JIT enabled
echo "Collecting data with JIT enabled (this may take a while)..."
echo "Running iterations from $START to $END..."

if [ -f results/data_jit.txt ]; then
    echo "Warning: results/data_jit.txt already exists. Appending will duplicate data."
    read -p "Remove existing file and start fresh? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm results/data_jit.txt
    fi
fi

for i in $(seq $START $STEP $END); do
    if [ $((i % 1000)) -eq 0 ]; then
        echo "Progress: $i / $END iterations"
    fi
    pypy -S "$SCRIPT" "$i" >> results/data_jit.txt
done

echo "JIT data collection complete!"
echo ""

# Collect data with JIT disabled
echo "Collecting data with JIT disabled (this may take a while)..."
echo "Running iterations from $START to $END..."

if [ -f results/data_nojit.txt ]; then
    echo "Warning: results/data_nojit.txt already exists. Appending will duplicate data."
    read -p "Remove existing file and start fresh? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm results/data_nojit.txt
    fi
fi

for i in $(seq $START $STEP $END); do
    if [ $((i % 1000)) -eq 0 ]; then
        echo "Progress: $i / $END iterations"
    fi
    pypy --jit off -S "$SCRIPT" "$i" >> results/data_nojit.txt
done

echo "No-JIT data collection complete!"
echo ""

# Collect CPython baseline data (optional, for comparison)
if command -v python3 &> /dev/null; then
    echo "Collecting CPython baseline data..."

    if [ -f results/data_cpython.txt ]; then
        echo "Warning: results/data_cpython.txt already exists."
        read -p "Remove existing file and start fresh? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm results/data_cpython.txt
        fi
    fi

    for i in $(seq $START $STEP $END); do
        if [ $((i % 1000)) -eq 0 ]; then
            echo "Progress: $i / $END iterations"
        fi
        python3 -S "$SCRIPT" "$i" >> results/data_cpython.txt
    done

    echo "CPython data collection complete!"
fi

echo ""
echo "All data collection complete!"
echo "Results saved in results/ directory:"
echo "  - results/data_jit.txt (PyPy with JIT)"
echo "  - results/data_nojit.txt (PyPy without JIT)"
if [ -f results/data_cpython.txt ]; then
    echo "  - results/data_cpython.txt (CPython baseline)"
fi
echo ""
echo "Run 'python plot_results.py' to visualize the data."
