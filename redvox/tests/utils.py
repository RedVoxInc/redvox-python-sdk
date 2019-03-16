import os

TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data")


def test_data(file: str) -> str:
    return os.path.join(TEST_DATA_DIR, file)
