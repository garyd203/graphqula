import pytest

from graphqula.error_handler import BaseErrorHandler
from graphqula.error_handler import FieldErrorData


class _StubErrorHandler(BaseErrorHandler):
    """Minimal concrete handler, so `BaseErrorHandler`'s shared behaviour is testable."""

    def report_error(self, message, *, child_field=None):
        return FieldErrorData(message=message)

    def report_exception(self, ex, *, child_field=None):
        return FieldErrorData(message=str(ex))


def test_bind_to_request_should_mark_handler_as_bound():
    # Setup
    handler = _StubErrorHandler()

    # Exercise
    handler.bind_to_request()

    # Verify
    assert handler.is_bound


def test_bind_to_request_should_reject_second_binding():
    # Setup
    handler = _StubErrorHandler()
    handler.bind_to_request()

    # Exercise / Verify
    with pytest.raises(Exception, match="single-use"):
        handler.bind_to_request()
