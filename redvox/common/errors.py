"""
This module contains custom error definitions used within this SDK.
"""

from typing import List


class RedVoxError(Exception):
    """
    This class represents generic RedVox SDK errors.
    """

    def __init__(self, message: str):
        super().__init__(f"RedVoxError: {message}")


class RedVoxExceptions:
    """
    This class represents multiple generic Redvox SDK errors for another class specified by obj_class.
    """

    def __init__(self, obj_class: str):
        self._obj_class = obj_class
        self._errors: List[RedVoxError] = []
        self._num_errors: int = 0

    def __repr__(self):
        return str(self.as_dict())

    def __str__(self):
        return str(self.as_dict())

    def get(self) -> List[RedVoxError]:
        """
        :return: the list of errors
        """
        return [a for a in self._errors]

    def append(self, msg: str):
        """
        append an error message to the list of errors

        :param msg: error message to add
        """
        self._errors.append(RedVoxError(f"{self._obj_class}: {msg}"))
        self._num_errors += 1

    def append_error(self, error: RedVoxError):
        """
        append an error to the list of errors

        :param error: error to add
        """
        self._errors.append(error)
        self._num_errors += 1

    def extend(self, msgs: List[str]):
        """
        extend a list of error messages to the list of errors

        :param msgs: error messages to add
        """
        self._errors.extend([RedVoxError(msg) for msg in msgs])
        self._num_errors += len(msgs)

    def extend_error(self, errors: "RedVoxExceptions"):
        """
        extend a list of error messages to the list of errors

        :param errors: errors to add
        """
        self._errors.extend(errors.get())
        self._num_errors += errors.get_num_errors()

    def get_num_errors(self) -> int:
        """
        :return: the number of errors
        """
        return self._num_errors

    def print(self):
        """
        print all errors
        """
        if self._num_errors > 0:
            print(f"Errors encountered while creating {self._obj_class}:")
            for error in self._errors:
                print(error)

    def as_dict(self) -> dict:
        """
        :return: self as dict
        """
        if self._num_errors > 0:
            return {
                "obj_class": self._obj_class,
                "num_errors": self._num_errors,
                "errors": [str(e) for e in self._errors]
            }
        return {"obj_class": self._obj_class}

    @staticmethod
    def from_dict(errors_dict: dict) -> "RedVoxExceptions":
        """
        :param errors_dict: dictionary representing a RedvoxExceptions object
        :return: RedvoxExceptions object
        """
        if "obj_class" not in errors_dict.keys():
            result = RedVoxExceptions("ExceptionsLoadFailure")
            result.append("Failed to load errors due to missing obj_class")
        else:
            result = RedVoxExceptions(errors_dict["obj_class"])
            if "errors" in errors_dict.keys():
                for er in errors_dict["errors"]:
                    result.append(er)
        return result
