import os
from unittest import TestCase

import redvox.settings as settings


class TestSettings(TestCase):
    def test_is_parallelism_enabled_env_none(self):
        self.assertIsNone(settings.is_parallelism_enabled_env())

    def test_is_parallelism_enabled_env_true(self):
        os.environ["REDVOX_ENABLE_PARALLELISM"] = "true"
        self.assertTrue(settings.is_parallelism_enabled_env())

    def test_is_parallelism_enabled_env_false(self):
        os.environ["REDVOX_ENABLE_PARALLELISM"] = "false"
        self.assertFalse(settings.is_parallelism_enabled_env())

    def test_is_parallelism_enabled_none(self):
        self.assertFalse(settings.is_parallelism_enabled())

    def test_is_parallelism_enabled_false(self):
        os.environ["REDVOX_ENABLE_PARALLELISM"] = "false"
        self.assertFalse(settings.is_parallelism_enabled())

    def test_is_parallelism_enabled_true(self):
        os.environ["REDVOX_ENABLE_PARALLELISM"] = "true"
        self.assertTrue(settings.is_parallelism_enabled())

    def test_set_parallelism_enabled_true(self):
        settings.set_parallelism_enabled(True)
        self.assertTrue(settings.is_parallelism_enabled())

    def test_set_parallelism_enabled_false(self):
        settings.set_parallelism_enabled(False)
        self.assertFalse(settings.is_parallelism_enabled())

