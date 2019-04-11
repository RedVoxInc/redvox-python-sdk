"""
This module provides functions for gracefully deprecating functionality in this SDK.
"""

import functools
import logging
import traceback
import typing

logger = logging.getLogger("DeprecationWarningLogger")


def deprecated(in_version: str, alt_fn: typing.Callable) -> typing.Callable:
    """
    Decorator used for deprecating functions in the SDK.
    This decorator will display a warning of the deprecated function being called, where it was called from, and then
    call the alternate function.
    :param in_version: Version that the function was deprecated in.
    :param alt_fn: An alternate function to use instead of the deprecated one.
    """
    def decorator_repeat(func):
        warn = "%s has been deprecated in version %s. Use %s instead." % (
            func.__name__,
            in_version,
            alt_fn.__name__)

        @functools.wraps(func)
        def wrapper_decorator(*args, **kwargs):
            tb = traceback.extract_stack(limit=2)[0]
            logger.warning("RedVox SDK Deprecation Warning: %s", warn)
            logger.warning(" -- %s %d %s", tb.filename, tb.lineno, tb.name)
            return alt_fn(*args, **kwargs)

        wrapper_decorator.__doc__ = warn
        return wrapper_decorator

    return decorator_repeat
