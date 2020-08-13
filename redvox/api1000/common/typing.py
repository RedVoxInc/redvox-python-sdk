"""
This module contains routines for type checking and inspection.
"""

from typing import Any, List, Optional, Callable, Union

import numpy as np

from redvox.api1000 import errors as errors


def check_type(value: Any,
               valid_types: List[Any],
               exception: Optional[Callable[[str], errors.ApiMError]] = None,
               additional_info: Optional[str] = None) -> None:
    """
    This provides some rudimentary type checking when setting API M data.
    This allows type errors to be a bit more consumable to users compared to errors thrown by the protobuf library. If
    the type check passes, nothing happens. If the type check fails, a customizable runtime exception is raised.
    :param value: The value to check the type of.
    :param valid_types: A list of valid types that the value may be.
    :param exception: An (optional) exception class which works with any exception that accepts a string as a single
                      argument. An ApiMError is raised by default.
    :param additional_info: Additional (optional) information to include in the error message. No additional information
                            is provided by default.
    """

    # It turns out that isinstance(True, int) will return True.... handle edge case first
    # https://stackoverflow.com/questions/37888620/comparing-boolean-and-int-using-isinstance
    if bool not in valid_types and isinstance(value, bool):
        # This is a bool and it shouldn't be, continue to issue logic
        pass
    else:
        if isinstance(value, tuple(valid_types)):
            return None

    # There are type check issues
    type_names: List[str] = list(map(lambda _valid_type: f"'{_valid_type.__name__}'", valid_types))
    message: str = f"Expected type(s) {' or '.join(type_names)}," \
                   f" but found '{type(value).__name__}'."

    if additional_info is not None:
        message += f" ({additional_info})"

    if exception is not None:
        raise exception(message)
    else:
        raise errors.ApiMTypeError(message)


def none_or_empty(value: Optional[Union[List, str, np.ndarray]]) -> bool:
    """
    Checks if the given value is None or empty.
    :param value: The value to check.
    :return: True if the value is None or empty, False otherwise.
    """
    if value is None:
        return True

    return len(value) == 0
