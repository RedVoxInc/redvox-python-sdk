"""
Provides global settings that tweak the inner workings of the SDK.
"""

import os
from typing import Optional

REDVOX_ENABLE_PARALLELISM_ENV: str = "REDVOX_ENABLE_PARALLELISM"


def is_parallelism_enabled_env() -> Optional[bool]:
    if REDVOX_ENABLE_PARALLELISM_ENV not in os.environ:
        return None

    env_val: str = os.environ.get(REDVOX_ENABLE_PARALLELISM_ENV).lower()
    if env_val == "true":
        return True
    elif env_val == "false":
        return False
    else:
        return None


__PARALLELISM_ENABLED: Optional[bool] = is_parallelism_enabled_env()


def set_parallelism_enabled(parallelism_enabled: bool) -> None:
    global __PARALLELISM_ENABLED
    __PARALLELISM_ENABLED = parallelism_enabled


def is_parallelism_enabled() -> bool:
    return True if __PARALLELISM_ENABLED is None else __PARALLELISM_ENABLED
