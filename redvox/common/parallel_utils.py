"""
Module that contains utilities for working with data in parallel.
"""

from enum import Enum
import multiprocessing
from multiprocessing.pool import Pool
from typing import Callable, Iterator, List, Optional, TypeVar

import numpy

import redvox.settings as settings

T = TypeVar("T")
R = TypeVar("R")


class MappingType(Enum):
    ParallelManaged: str = "ParallelManaged"
    ParallelUnmanaged: str = "ParallelUnmanaged"
    Serial: str = "Serial"


def maybe_parallel_map(pool: Optional[Pool],
                       map_fn: Callable[[T], R],
                       iterator: Iterator[T],
                       condition: Optional[Callable[[], bool]] = None,
                       chunk_size: int = 64,
                       usage_out: Optional[List[MappingType]] = None) -> Iterator[R]:
    """
    Maps a function over a set of values. This will either be run in parallel or serially depending on the value
    of redvox.settings.

    :param pool: An optional pool. If a pool is provided, the user is responsible for closing the pool. If the pool
                 is not provided, one is created by this process and then closed at the end of this process.
    :param map_fn: A function that maps each value in the provided iterator.
    :param iterator: An iterator of elements to be mapped.
    :param condition: An optional condition, that when provided, will be checked and if the condition passes, this
                      function may run in parallel. This is useful for things like, only run in parallel if more than
                      n entries are provided.
    :param chunk_size: An optional chunk side to pass to parallel maps.
    :param usage_out: When provided, this value will be filled with a single value
                      describing which mapping strategy was used.
    :return: A transformed iterator.
    """

    def __usage_out(mapping_type: MappingType) -> None:
        if usage_out is not None:
            usage_out.append(mapping_type)

    # If a condition is not provided, then it's always True.
    _condition: bool = True if condition is None else condition()
    res: R
    if settings.is_parallelism_enabled() and _condition:
        _pool: Pool = multiprocessing.Pool() if pool is None else pool
        for res in _pool.imap(map_fn, iterator, chunksize=chunk_size):
            yield res

        # If we're managing this pool, close it.
        if pool is None:
            __usage_out(MappingType.ParallelManaged)
            _pool.close()
        else:
            __usage_out(MappingType.ParallelUnmanaged)
    else:
        # Run serially
        __usage_out(MappingType.Serial)
        for res in map(map_fn, iterator):
            yield res


def maybe_parallel_smap(pool: Optional[Pool],
                        map_fn: Callable[[T], R],
                        iterator: List[Iterator[T]],
                        condition: Optional[Callable[[], bool]] = None,
                        chunk_size: int = 64,
                        usage_out: Optional[List[MappingType]] = None) -> Iterator[R]:
    """
    Maps a function over a set of values. This will either be run in parallel or serially depending on the value
    of redvox.settings.  accepts multiple arguments for the function

    :param pool: An optional pool. If a pool is provided, the user is responsible for closing the pool. If the pool
                 is not provided, one is created by this process and then closed at the end of this process.
    :param map_fn: A function that maps each value in the provided iterator.
    :param iterator: A list of iterator of elements to be mapped.
    :param condition: An optional condition, that when provided, will be checked and if the condition passes, this
                      function may run in parallel. This is useful for things like, only run in parallel if more than
                      n entries are provided.
    :param chunk_size: An optional chunk side to pass to parallel maps.
    :param usage_out: When provided, this value will be filled with a single value
                      describing which mapping strategy was used.
    :return: A transformed iterator.
    """

    def __usage_out(mapping_type: MappingType) -> None:
        if usage_out is not None:
            usage_out.append(mapping_type)

    # If a condition is not provided, then it's always True.
    _condition: bool = True if condition is None else condition()
    res: R
    if settings.is_parallelism_enabled() and _condition:
        _pool: Pool = multiprocessing.Pool() if pool is None else pool
        for res in _pool.starmap(map_fn, iterator, chunksize=chunk_size):
            yield res

        # If we're managing this pool, close it.
        if pool is None:
            __usage_out(MappingType.ParallelManaged)
            _pool.close()
        else:
            __usage_out(MappingType.ParallelUnmanaged)
    else:
        # Run serially
        __usage_out(MappingType.Serial)
        for res in map(map_fn, *iterator):
            yield res
