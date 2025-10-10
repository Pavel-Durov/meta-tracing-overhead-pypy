"""
PyPy Meta-Tracing JIT Overhead Benchmark

This script replicates the benchmark from Carl Friedrich Bolz-Tereick's blog post:
https://cfbolz.de/posts/speed-of-tracing/

The benchmark measures the overhead of PyPy's meta-tracing interpreter by running
100 replicated versions of a simple function with varying iteration counts.


This function is the ideal case for PyPy's JIT compiler, as it has a
tight loop with many object allocations that all have predictable
lifetimes. There is no control flow inside the loop. The JIT compiler
can optimize this loop body extremely well, to just an integer addition.
"""

# from __future__ import print_function
import sys
import time

all_funcs = []
all_results = set()
s = """
class A%s(object):
    pass

def main%s():
    res = 0
    for i in range(num):
        a = A%s()
        a.x = i
        d = {"a": a.x}
        l = [0, 1, d["a"]]
        res += l[-1]
    all_results.add(res)
all_funcs.append(main%s)
"""
program = "\n".join(s % (i, i, i, i) for i in range(100))
exec(program)

# Number of iterations
num = int(sys.argv[1])

t1 = time.time()
for fn in all_funcs:
    fn()
t2 = time.time()
print(num, t2 - t1)