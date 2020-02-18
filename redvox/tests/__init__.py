"""
Tests module
"""

import os.path

TEST_DATA_DIR: str = os.path.join(os.path.dirname(__file__), "test_data")


def test_data_path(resource: str) -> str:
    """
    Returns the absolute path of a test resource.
    :param resource: The name of the resource.
    :return: The absolute path of a test resource.
    """
    return os.path.join(TEST_DATA_DIR, resource)
