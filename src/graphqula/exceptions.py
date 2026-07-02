from __future__ import annotations


class CancelledExecutionError(Exception):
    """Generic error raised when GraphQL execution is cancelled before all response data was determined."""


class SchemaFrozenError(Exception):
    """Raised when we try to modify a frozen schema."""
