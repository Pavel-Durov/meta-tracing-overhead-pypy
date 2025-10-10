# Benchmark Scripts

This directory contains different benchmark scripts for measuring PyPy's meta-tracing JIT overhead.

## Available Benchmarks

### `benchmark.py` (Default - Allocation-Heavy)
**Location:** `../benchmark.py`

The original benchmark from [Carl Friedrich Bolz-Tereick's blog post](https://cfbolz.de/posts/speed-of-tracing/). This benchmark focuses on:
- Object allocation (`A()`)
- Attribute assignment (`a.x = i`)
- Dictionary operations (`d = {"a": a.x}`)
- List operations (`l = [0, 1, d["a"]]`)
- Integer addition (`res += l[-1]`)

**Characteristics:**
- Allocation-heavy workload
- Ideal case for PyPy's JIT (predictable object lifetimes)
- Can achieve ~200x speedup after JIT warmup
- Best for testing allocation/escape analysis optimizations

**Usage:**
```bash
# Default benchmark (no need to specify)
uv run python main.py run

# Or explicitly
uv run python main.py run --benchmark-script benchmark.py
```

### `fib.py` - Fibonacci (Computation-Heavy)
**Location:** `benchmarks/fib.py`

A recursive Fibonacci computation benchmark. This benchmark focuses on:
- Recursive function calls
- Pure computation (minimal allocation)
- Branch prediction
- Call stack management

**Characteristics:**
- Computation-heavy workload
- Tests JIT optimization of recursive functions
- More representative of mathematical/computational workloads
- Demonstrates function inlining and call optimizations

**Usage:**
```bash
uv run python main.py run --benchmark-script benchmarks/fib.py
```

### `original.py` - Reference Implementation
**Location:** `benchmarks/original.py`

A preserved copy of the original benchmark for reference purposes.

## Creating Custom Benchmarks

To create your own benchmark, follow this structure:

```python
"""
Your Benchmark Description
"""
import sys
import time

all_funcs = []
all_results = set()

# Generate 100 replicated functions
s = """
def main%s():
    res = 0
    for i in range(num):
        # Your benchmark code here
        res += i
    all_results.add(res)
all_funcs.append(main%s)
"""
program = "\n".join(s % (i, i) for i in range(100))
exec(program)

# Number of iterations from command line
num = int(sys.argv[1])

# Time execution
t1 = time.time()
for fn in all_funcs:
    fn()
t2 = time.time()

# Output: <iterations> <time_in_seconds>
print(num, t2 - t1)
```

### Requirements

1. **Accept iterations as first argument**: `num = int(sys.argv[1])`
2. **Output format**: `print(num, elapsed_time)`
3. **100 replicated functions**: Helps reduce measurement noise
4. **Use global `num` variable**: Functions access this during execution

### Testing Your Benchmark

```bash
# Test with Python
python3 your_benchmark.py 100

# Test with PyPy
pypy3 your_benchmark.py 100

# Run full analysis
uv run python main.py run --benchmark-script your_benchmark.py
```

## Benchmark Comparison

| Benchmark | Type | Primary Focus | JIT Benefits |
|-----------|------|---------------|--------------|
| `benchmark.py` | Allocation | Object creation, dictionaries, lists | Very High (~200x) |
| `fib.py` | Computation | Recursive calls, pure computation | High |

## Usage Examples

### Quick Test (50 iterations)
```bash
uv run python main.py run --benchmark-script benchmarks/fib.py --end 50
```

### Full Analysis
```bash
uv run python main.py run --benchmark-script benchmarks/fib.py \
    --start 1 --end 20000 --step 1
```

### Compare Different Benchmarks
```bash
# Run allocation benchmark
uv run python main.py run --output-dir results/allocation-2025

# Run computation benchmark
uv run python main.py run --benchmark-script benchmarks/fib.py \
    --output-dir results/computation-2025

# Compare the plots in each directory
```

## Performance Notes

- **Allocation benchmark**: Faster per iteration, ideal for JIT testing
- **Fibonacci benchmark**: Slower per iteration, better for computation testing
- Adjust `--end` and `--step` values based on benchmark speed
- Use `--collect-jit-logs` to capture detailed JIT compilation statistics

## References

- Original blog post: https://cfbolz.de/posts/speed-of-tracing/
- PyPy JIT documentation: https://doc.pypy.org/en/latest/jit/index.html

