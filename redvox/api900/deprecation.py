import functools
import logging
import traceback

logger = logging.getLogger("DeprecationWarningLogger")


def deprecated(in_version: str, alt_fn):
    def decorator_repeat(func):
        @functools.wraps(func)
        def wrapper_decorator(*args, **kwargs):
            tb = traceback.extract_stack(limit=2)[0]
            logger.warning("RedVox SDK Deprecation Warning: %s has been deprecated in version %s. Use %s instead.",
                           func.__name__,
                           in_version,
                           alt_fn.__name__)
            logger.warning(" -- %s %d %s", tb.filename, tb.lineno, tb.name)
            func(*args, **kwargs)

        return wrapper_decorator

    return decorator_repeat
