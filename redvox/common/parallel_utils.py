from multiprocessing import cpu_count, Pool
import multiprocessing.pool
from typing import Optional

__pool: Optional[multiprocessing.pool.Pool] = None


def pool() -> multiprocessing.pool.Pool:
    global __pool
    if __pool is None:
        __pool = Pool(cpu_count())
    return __pool
