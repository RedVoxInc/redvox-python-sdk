from enum import Enum


def wrap_enum(proto_type):
    def __wrap_enum(enum: Enum) -> Enum:
        setattr(enum, "into_proto", lambda self: proto_type.Value(self.name))
        # noinspection PyCallingNonCallable
        enum.from_proto = staticmethod(lambda proto: enum(proto))
        return enum

    return __wrap_enum



