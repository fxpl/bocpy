"""
To run this benchmark you need to clone `https://github.com/fxpl/cpython` and
build the `tracing-region` branch.

make clean
./configure --enable-optimizations
make -j

Then build a virtual environment in the root of this repo and install the bocpy
repo on the `tracing-regions` branch. And then run the benchmark:

../cpython/python.exe -m venv .venvpyrona
source .venvpyrona/bin/activate.fish
pip install -e . --verbose

python pyrona.py
"""


import random
import time
import statistics

from immutable import TracingRegion as Region
from bocpy import Cown, when, wait

SEED = 0

class Node:
    def __init__(self, value=None):
        self.value = value
        self.left = None
        self.right = None

    def insert(self, value):
        if self.value is None:      # empty root
            self.value = value
            return
        node = self
        while True:
            if value < node.value:
                if node.left is None:
                    node.left = Node(value)
                    return
                node = node.left
            else:
                if node.right is None:
                    node.right = Node(value)
                    return
                node = node.right

def populate(c: Cown, size: int = 10):
    random.seed(SEED)
    tree = Node()
    for _ in range(size):
        tree.insert(random.randint(0, 2**31 - 1))

    with c:
        c.value.x = tree
        tree = None

def _summary(samples):
    return {
        "min": min(samples),
        "median": statistics.median(samples),
        "mean": statistics.mean(samples),
        "max": max(samples),
        "std": statistics.stdev(samples) if len(samples) > 1 else 0.0,
    }

def benchmark_data(c: Cown, trials: int = 100, warmup: int = 10):
    acquire, release = [], []

    for i in range(warmup + trials):
        t0 = time.perf_counter_ns()
        c.acquire()
        t1 = time.perf_counter_ns()

        c.release()
        t2 = time.perf_counter_ns()

        if i >= warmup:
            acquire.append((t1 - t0) / 1000.0)   # ns -> µs
            release.append((t2 - t1) / 1000.0)

    return {"acquire": _summary(acquire), "release": _summary(release)}

class A: pass

def main():
    print(f"{'size':>5}, {'impl':<13}, {'op':<7}, "
          f"{'min_us':>12}, {'median_us':>12}, {'mean_us':>12}, "
          f"{'max_us':>12}, {'std_us':>12}")

    for size in [1, 10, 100, 1000, 10000]:
        c = Cown()
        with c:
            c.value = Region()
        populate(c, size)
        res1 = benchmark_data(c)
        # This will raise an exception if something failed previously
        out = c.unwrap()
        assert(out.x is not None)

        c = Cown()
        with c:
            c.value = A()
        populate(c, size)
        res2 = benchmark_data(c)
        # This will raise an exception if something failed previously
        out = c.unwrap()
        assert(out.x is not None)

        for impl, res in (("TracingRegion", res1), ("Pickling", res2)):
            for op in ("acquire", "release"):
                s = res[op]
                print(f"{size:>5}, {impl:<13}, {op:<7}, "
                      f"{s['min']:>12.4f}, {s['median']:>12.4f}, {s['mean']:>12.4f}, "
                      f"{s['max']:>12.4f}, {s['std']:>12.4f}")

    stats = wait(stats=True)
    print(stats)

if __name__ == "__main__":
    main()




