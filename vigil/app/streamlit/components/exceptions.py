class VigilAPIError(Exception):
    """Raised when the Vigil API returns an unexpected error."""


class VigilConnectionError(VigilAPIError):
    """Raised when the dashboard cannot reach the Vigil API."""


class VigilNotFoundError(VigilAPIError):
    """Raised when the requested resource does not exist."""
