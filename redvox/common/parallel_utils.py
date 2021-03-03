"""
This module provides a lazy singleton of a process pool.
"""

from multiprocessing import cpu_count, Pool
import multiprocessing.pool
from typing import Optional

__pool: Optional[multiprocessing.pool.Pool] = None


def pool() -> multiprocessing.pool.Pool:
    """
    :return: An instance of a process pool if one exists, otherwise, one is created and returned.
    """
    global __pool
    if __pool is None:
        __pool = Pool(cpu_count())
    return __pool
