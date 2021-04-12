import multiprocessing
from multiprocessing.pool import Pool
from typing import Callable, Iterator, Optional, TypeVar

import redvox.settings as settings

T = TypeVar("T")
R = TypeVar("R")


def maybe_parallel_map(pool: Optional[Pool],
                       map_fn: Callable[[T], R],
                       iterator: Iterator[T],
                       condition: Optional[Callable[[],  bool]] = None,
                       chunk_size: int = 64) -> Iterator[R]:
    _condition: bool = True if condition is None else condition()
    res: R
    if settings.is_parallelism_enabled() and _condition:
        _pool: Pool = multiprocessing.Pool() if pool is None else pool
        for res in _pool.imap(map_fn, iterator, chunksize=chunk_size):
            yield res
        if pool is None:
            _pool.close()
    else:
        for res in map(map_fn, iterator):
            yield res
