import time
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def timeit(label: str) -> Iterator[None]:
    start_time = time.time()
    yield
    end_time = time.time()
    print(f"{label}: {end_time - start_time:.6f} seconds")
