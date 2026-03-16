class AppException(Exception):
    def __init__(self, message: str = "An error occurred"):
        self.message = message
        super().__init__(self.message)


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message)


class ConflictError(AppException):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message)


class AuthenticationRequired(Exception):
    def __init__(self, redirect_url: str = "/auth/login"):
        self.redirect_url = redirect_url
        super().__init__(f"Authentication required: {redirect_url}")
