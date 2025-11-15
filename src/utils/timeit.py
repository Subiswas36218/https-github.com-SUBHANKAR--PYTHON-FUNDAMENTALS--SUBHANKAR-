from contextlib import contextmanager
import time
from typing import Iterator


@contextmanager
def timeit(label: str) -> Iterator[None]:
    start_time = time.time()
    yield
    end_time = time.time()
    print(f"{label}: {end_time - start_time:.6f} seconds")