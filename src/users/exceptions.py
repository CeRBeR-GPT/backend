from fastapi import HTTPException, status


class InvalidOAuthStateException(HTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Invalid OAuth2 state"

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class OAuthServiceNotFoundException(HTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "This OAuth service not found"

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class OAuthTokenNotFoundException(HTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Failed to obtain tokens"

    def __init__(self, service_name: str):
        self.detail += f" from {service_name}"
        super().__init__(status_code=self.status_code, detail=self.detail)


class FetchingGitHubUserException(HTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Failed to fetch user info from GitHub"

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class EmailExistsException(HTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "User with this email already exists"

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class ShortNameExistsException(HTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "User with this shortname already exists"

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class CredentialException(HTTPException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Could not validate credentials"
    headers = {"WWW-Authenticate": "Bearer"}

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail, headers=self.headers)


class TokenTypeException(HTTPException):

    def __new__(cls, *args, **kwargs):
        cls.detail = f"Invalid token type {args[0]!r} expected {args[1]!r}"
        cls.status_code = status.HTTP_401_UNAUTHORIZED

        return super().__new__(cls)

    def __init__(self, *args):  # noqa
        super().__init__(status_code=self.status_code, detail=self.detail)


class CodeTypeException(HTTPException):
    def __new__(cls, *args, **kwargs):
        cls.detail = f"Invalid code type {args[0]!r} expected {args[1]!r}"
        cls.status_code = status.HTTP_401_UNAUTHORIZED

        return super().__new__(cls)

    def __init__(self, *args):  # noqa
        super().__init__(status_code=self.status_code, detail=self.detail)


class TooLargeFileException(HTTPException):
    def __new__(cls, *args, **kwargs):
        cls.detail = f"Your file size {args[0]!r} bytes, need less {args[1]!r} bytes"
        cls.status_code = status.HTTP_400_BAD_REQUEST

        return super().__new__(cls)

    def __init__(self, *args):  # noqa
        super().__init__(status_code=self.status_code, detail=self.detail)


class UserNotFoundException(HTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "User not found"

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class AccessException(HTTPException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Access denied!"

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class EmailSenderException(HTTPException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Failed to send code to email"

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class IncorrectEmailAddressException(HTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Invalid email address"

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class IncorrectVerifyCodeException(HTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Incorrect verification code"

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)
