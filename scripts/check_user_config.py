#!/usr/bin/env python3

"""
When generating API documentation, we do now want saved RedVoxConfigurations secrets to be leaked into the API
documentation.

This script checks for the present of RedVox config fields in both the environment and in the home directory.
"""

import sys

from redvox.cloud.config import RedVoxConfig


def main() -> bool:
    try:
        RedVoxConfig.from_env()
        print("Found RedVox configuration in environment")
        return True
    except:
        pass

    try:
        RedVoxConfig.from_home()
        print("Found RedVox configuration in user's home directory")
        return True
    except:
        pass

    return False


if __name__ == '__main__':
    if main():
        sys.exit(1)
