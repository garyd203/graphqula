"""Interfaces and multiple concrete implementations for handling errors within a deferred field function."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Sequence

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class FieldErrorData:
    """Client-facing data for an error that occurred whilst evaluating a field.

    GraphQL allows for lenient error handling with partial responses, so we use this
    to capture details when a field could not be evaluated, but the error was handled.
    """

    # TODO needs a `path` (list[str | int]) to the failing field, and probably
    #   `locations`/`extensions`, to be spec-faithful. Deferred until path-tracking
    #   through the resolver tree is designed.
    # TODO Make this contain useful fields, regardless of whether they are used in the "official" error reporting output
    message: str


class CancelledExecutionError(Exception):
    """Generic error raised when GraphQL execution is cancelled before all response data was determined."""


class ErrorHandler(ABC):
    """Interface for handling errors that occur during field evaluation.

    GraphQL allows for partial responses if an execution error partway down the request
    graph can be safely suppressed. This handler allows us to implement alternative
    strategies, such as error-accumulation or fail-fast.

    Instances of concrete ErrorHandler subclasses are single-use, bound to a specific execution.
    """

    @abstractmethod
    def report_error(
        self, message: str, *, child_field: str | None = None
    ) -> FieldErrorData:
        """Report an error that occurred whilst evaluating the current field, using a plain error message.

        After reporting the error, the caller should set the value of the error-ing
        field to a suitable value, such as None.

        Params:
            message: A safe user-facing natural language message describing the error.
            child_field: If the error occurred whilst evaluating a direct child, then
                this should be set to the name of that field, so that the graph path
                in the error data is set correctly.

        Returns:
            The full details of this error, as they would be reported to the caller.

        Raises:
            CancelledExecutionError if this ErrorHandler decides to end request
                execution.
        """
        pass

    @abstractmethod
    def report_exception(
        self, ex: Exception, *, child_field: str | None = None
    ) -> FieldErrorData:
        """Report an unhandled exception that was caught whilst evaluating the current field.

        After reporting the error, the caller should set the value of the error-ing
        field to a suitable value, such as None.

        Params:
            ex: The exception that caused the error.
            child_field: If the error occurred whilst evaluating a direct child, then
                this should be set to the name of that field, so that the graph path
                in the error data is set correctly.

        Returns:
            The full details of this error, as they would be reported to the caller.

        Raises:
            The original exception if this ErrorHandler decides to end request
                execution.
        """
        pass


@dataclass()
class BaseErrorHandler(ErrorHandler, ABC):
    """Base implementation for all concrete `ErrorHandler` implementations."""

    # TODO maybe pull out a SingleUseObject base class.

    is_bound: bool = False

    def bind_to_request(self) -> None:
        """Bind this single-use error handler to the current GraphQL request.

        This should be called at the beginning of `execute()`.
        """
        if self.is_bound:
            raise Exception("Attempting to re-use a single-use ErrorHandler instance.")
        self.is_bound = True


class FailFastErrorHandler(BaseErrorHandler):
    """Error handling strategy that cancels execution when any error is reported,
    by raising an exception.

    Raises the original exception, or else `CancelledExecutionError` if the reported
    error was not an exception.
    """

    def report_error(
        self, message: str, *, child_field: str | None = None
    ) -> FieldErrorData:
        raise CancelledExecutionError(message)

    def report_exception(
        self, ex: Exception, *, child_field: str | None = None
    ) -> FieldErrorData:
        raise ex


@dataclass()
class ErrorTracker(BaseErrorHandler):
    """Error handling strategy that records all errors for later reference,
    allowing the caller to return partial results when possible.
    """

    _errors: list[FieldErrorData] = field(default_factory=list)

    def get_errors(self) -> Sequence[FieldErrorData]:
        """Read-only view of all errors encountered so far, in the order they occurred in."""
        # Create a copy so that callers can't accidentally update the error list.
        # Use tuple so that it's obviously a read-only sequence.
        return tuple(self._errors)

    def report_error(
        self, message: str, *, child_field: str | None = None
    ) -> FieldErrorData:
        # TODO thread- and async- safe would be nice
        # TODO should add more context to this log message, such as field name
        LOGGER.warning("Handled error evaluating field: %s", message)
        return self._track_error(message)

    def report_exception(
        self, ex: Exception, *, child_field: str | None = None
    ) -> FieldErrorData:
        # TODO should add more context to this log message, such as field name
        LOGGER.warning("Handled error evaluating field: %s", str(ex), exc_info=True)
        return self._track_error(str(ex))

    def _track_error(self, message: str) -> FieldErrorData:
        data = FieldErrorData(message=message)
        self._errors.append(data)
        return data


@dataclass()
class BoundedErrorTracker(ErrorTracker):
    """Error handling strategy that records all errors for later reference,
    but cancels execution if there are too many errors.
    """

    max_errors: int = 5

    def __post_init__(self) -> None:
        if self.max_errors < 1:
            raise ValueError("Error limit must be non-zero")

    def _check_error_count(self):
        if len(self._errors) > self.max_errors:
            # TODO should add more context to this log message, such as the list of original errors
            LOGGER.error("Too many errors occurred, cancelling request execution")

            failure_message = "Too many errors found during evaluation: " + "; ".join(
                f'"{e.message}"' for e in self._errors
            )
            raise CancelledExecutionError(failure_message)

    def report_error(
        self, message: str, *, child_field: str | None = None
    ) -> FieldErrorData:
        data = super().report_error(message, child_field=child_field)
        self._check_error_count()
        return data

    def report_exception(
        self, ex: Exception, *, child_field: str | None = None
    ) -> FieldErrorData:
        data = super().report_exception(ex, child_field=child_field)
        self._check_error_count()
        return data
