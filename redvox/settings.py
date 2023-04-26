"""
Provides global settings that tweak the inner workings of the SDK.
"""

import os
from typing import Optional

REDVOX_ENABLE_PARALLELISM_ENV: str = "REDVOX_ENABLE_PARALLELISM"


def is_parallelism_enabled_env() -> Optional[bool]:
    """
    Tests if parallelism is enabled or disabled by checking the presence and value of an environmental variable.
    If the env var DNE, None is returned. If the env var does exist, it is parsed as either "true" or "false" into
    the corresponding boolean and returned. If the env var exists, but is not one of "true" or "false", None is
    returned.
    :return: Either True or False if the env var exists and can be parsed or None.
    """
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
    """
    Sets whether parallelism is enabled or disabled within the SDK.
    :param parallelism_enabled: True to enable, False otherwise
    """
    global __PARALLELISM_ENABLED
    __PARALLELISM_ENABLED = parallelism_enabled


def is_parallelism_enabled() -> bool:
    """
    Returns whether or not parallelism is enabled with the SDK.
    :return: Whether or not parallelism is enabled with the SDK.
    """
    global __PARALLELISM_ENABLED
    if __PARALLELISM_ENABLED is None:
        __PARALLELISM_ENABLED = is_parallelism_enabled_env()
    return False if __PARALLELISM_ENABLED is None else __PARALLELISM_ENABLED


def is_gui_extra_enabled() -> bool:
    """
    :return: True if the GUI extra is enabled, False otherwise
    """
    try:
        import matplotlib
        import PySide6
        return True
    except ModuleNotFoundError:
        return False


def is_native_extra_enabled() -> bool:
    """
    :return: True if the native extra is enabled, False otherwise
    """
    try:
        import redvox_native
        return True
    except ModuleNotFoundError:
        return False
