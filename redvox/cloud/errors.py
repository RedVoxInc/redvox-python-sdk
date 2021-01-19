"""
Custom defined RedVox Cloud derived errors.
"""


class CloudApiError(Exception):
    """
    A generic Cloud API error.
    """


class AuthenticationError(CloudApiError):
    """
    A cloud authentication error.
    """

    def __init__(self):
        super().__init__("Authentication Error")


class ApiConnectionError(CloudApiError):
    """
    A connection error.
    """

    def __init__(self, message: str = ""):
        super().__init__(f"ApiConnectionError: {message}")
