from __future__ import annotations


class CancelledExecutionError(Exception):
    """Generic error raised when GraphQL execution is cancelled before all response data was determined."""
