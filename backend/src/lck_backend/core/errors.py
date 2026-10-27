from fastapi import HTTPException, status


class LCKBaseException(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ManifestValidationError(LCKBaseException):
    def __init__(self, message: str):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)


class KnowledgeSnapshotError(LCKBaseException):
    def __init__(self, message: str):
        super().__init__(message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AuthenticationError(LCKBaseException):
    def __init__(self, message: str = "Invalid or missing authorization token"):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED)


class GuardrailRejectedError(LCKBaseException):
    def __init__(self, reason: str, message: str):
        self.reason = reason
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)


class InsufficientEvidenceError(LCKBaseException):
    def __init__(self, message: str = "I cannot find this information in the official airport knowledge base."):
        super().__init__(message=message, status_code=status.HTTP_200_OK)

