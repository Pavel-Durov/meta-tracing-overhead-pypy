"""
Fibonacci Benchmark for PyPy JIT Analysis

This benchmark computes Fibonacci numbers to measure JIT compilation overhead.
Unlike the allocation-heavy original benchmark, this focuses on computation.
"""
import sys
import time

all_funcs = []
all_results = set()

# Generate 100 replicated Fibonacci functions
s = """
def fib%s(n):
    if n <= 1:
        return n
    return fib%s(n - 1) + fib%s(n - 2)

def main%s():
    res = 0
    for i in range(num):
        # Compute Fibonacci of a small number to keep it reasonably fast
        # but still trigger JIT compilation
        res += fib%s(min(i %% 20, 15))
    all_results.add(res)
all_funcs.append(main%s)
"""
program = "\n".join(s % (i, i, i, i, i, i) for i in range(100))
exec(program)

# Number of iterations
num = int(sys.argv[1])

t1 = time.time()
for fn in all_funcs:
    fn()
t2 = time.time()
print(num, t2 - t1)