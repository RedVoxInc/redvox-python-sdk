"""
This module provides decorators used throughout the API M SDK codebase.
"""
from enum import Enum

from google.protobuf.internal.enum_type_wrapper import EnumTypeWrapper


def wrap_enum(proto_type: EnumTypeWrapper):
    """
    Decorator that provides automatic conversion methods to convert between the protobuf enum and the SDK provided enum.
    Will add an into_proto(self) method and a from_proto(proto) dynamically to Python standard enum.Enum classes.
    :param proto_type: The protobuf type
    :return: A function for decorating Python enums.
    """
    def __wrap_enum(enum: Enum) -> Enum:
        """
        Wrapper function for decorating enums.
        :param enum: The Python enum to decorate.
        :return: The decorated enumeration with dynamic methods set
        """
        setattr(enum, "into_proto", lambda self: proto_type.Value(self.name))
        # noinspection Mypy, PyCallingNonCallable
        enum.from_proto = staticmethod(lambda proto: enum(proto))
        return enum

    return __wrap_enum



