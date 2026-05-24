class AppError(Exception):
    """Base application exception."""


class InsufficientEvidenceError(AppError):
    """Raised when retrieved evidence is not enough for a grounded answer."""
