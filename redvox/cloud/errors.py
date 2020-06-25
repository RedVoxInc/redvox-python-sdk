class CloudApiError(Exception):
    def __init__(self, message: str = ""):
        super().__init__(message)


class AuthenticationError(CloudApiError):
    def __init__(self):
        super().__init__("Authentication Error")


class ApiConnectionError(CloudApiError):
    def __init__(self, message: str = ""):
        super().__init__(f"ApiConnectionError: {message}")
