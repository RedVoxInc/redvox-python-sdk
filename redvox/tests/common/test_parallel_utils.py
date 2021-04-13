from typing import List
from unittest import TestCase
from multiprocessing import Pool

import redvox.settings as settings
from redvox.common.parallel_utils import maybe_parallel_map, MappingType

def map_fn(v: int) -> str:
    return str(v * v)

class TestParallelUtils(TestCase):
    def setUp(self) -> None:
        self.data: List[int] = list(range(10))
        self.res: List[str] = ["0", "1", "4", "9", "16", "25", "36", "49", "64", "81"]

    def test_normal_provided_pool(self):
        settings.set_parallelism_enabled(True)
        pool = Pool()
        usage_out = []
        res = maybe_parallel_map(pool, map_fn, self.data, usage_out=usage_out)
        self.assertEqual(self.res, list(res))
        self.assertEqual(MappingType.ParallelUnmanaged, usage_out[0])
        pool.close()
        settings.set_parallelism_enabled(False)

    def test_normal_managed_pool(self):
        settings.set_parallelism_enabled(True)
        usage_out = []
        res = maybe_parallel_map(None, map_fn, self.data, usage_out=usage_out)
        self.assertEqual(self.res, list(res))
        self.assertEqual(MappingType.ParallelManaged, usage_out[0])
        settings.set_parallelism_enabled(False)

    def test_normal_serial(self):
        settings.set_parallelism_enabled(False)
        usage_out = []
        res = maybe_parallel_map(None, map_fn, self.data, usage_out=usage_out)
        self.assertEqual(self.res, list(res))
        self.assertEqual(MappingType.Serial, usage_out[0])

    def test_parallel_condition_good(self):
        settings.set_parallelism_enabled(True)
        usage_out = []
        res = maybe_parallel_map(None, map_fn, self.data, usage_out=usage_out, condition=lambda: len(self.data) >= 10)
        self.assertEqual(self.res, list(res))
        self.assertEqual(MappingType.ParallelManaged, usage_out[0])
        settings.set_parallelism_enabled(False)

    def test_parallel_condition_bad(self):
        settings.set_parallelism_enabled(True)
        usage_out = []
        res = maybe_parallel_map(None, map_fn, self.data, usage_out=usage_out, condition=lambda: len(self.data) > 10)
        self.assertEqual(self.res, list(res))
        self.assertEqual(MappingType.Serial, usage_out[0])
        settings.set_parallelism_enabled(False)