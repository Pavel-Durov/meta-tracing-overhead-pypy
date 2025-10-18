"""
List Operations Benchmark for PyPy JIT Analysis

Simple list creation and access operations.
Tests JIT optimization of list operations and indexing.
"""
import sys
import time

all_funcs = []
all_results = set()

# Generate 100 replicated list operation functions
s = """
def main%s():
    res = 0
    for i in range(num):
        lst = [i, i+1, i+2, i+3, i+4]
        res += lst[0] + lst[2] + lst[4]
    all_results.add(res)
all_funcs.append(main%s)
"""
program = "\n".join(s % (i, i) for i in range(100))
exec(program)

# Number of iterations
num = int(sys.argv[1])

t1 = time.time()
for fn in all_funcs:
    fn()
t2 = time.time()
print(num, t2 - t1)

