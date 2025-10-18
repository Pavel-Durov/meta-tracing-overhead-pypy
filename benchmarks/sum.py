"""
Simple Sum Benchmark for PyPy JIT Analysis

The simplest possible benchmark - just integer addition in a loop.
Tests basic loop optimization and integer arithmetic JIT compilation.
"""
import sys
import time

all_funcs = []
all_results = set()


program = "\n".join(f"""

def main{i}():
    res = 0
    for i in range(num):
        res += i
    all_results.add(res)
all_funcs.append(main{i})

""" for i in range(100))
exec(program)

# Number of iterations
num = int(sys.argv[1])

t1 = time.time()
for fn in all_funcs:
    fn()
t2 = time.time()
print(num, t2 - t1)

