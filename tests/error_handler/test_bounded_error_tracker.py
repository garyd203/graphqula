import logging

import pytest

from graphqula.error_handler import BoundedErrorTracker
from graphqula.error_handler import CancelledExecutionError


def test_should_reject_zero_error_limit_in_configuration():
    # Exercise / Verify
    with pytest.raises(ValueError, match="non-zero"):
        BoundedErrorTracker(max_errors=0)


def test_should_reject_negative_error_limit_in_configuration():
    # Exercise / Verify
    with pytest.raises(ValueError, match="non-zero"):
        BoundedErrorTracker(max_errors=-52)


def test_should_record_errors_up_to_the_limit():
    # Setup
    tracker = BoundedErrorTracker(max_errors=2)

    # Exercise
    tracker.report_error("first")
    tracker.report_error("second")

    # Verify
    assert len(tracker.get_errors()) == 2


def test_should_raise_error_when_limit_exceeded():
    # Setup
    tracker = BoundedErrorTracker(max_errors=2)
    tracker.report_error("first")
    tracker.report_error("second")

    # Exercise / Verify
    with pytest.raises(CancelledExecutionError, match="Too many errors"):
        tracker.report_error("third")


def test_should_log_error_message_when_cancelling(caplog):
    # Setup
    caplog.set_level(logging.ERROR)

    tracker = BoundedErrorTracker(max_errors=1)
    tracker.report_error("first")

    # Exercise
    with pytest.raises(CancelledExecutionError, match="Too many errors"):
        tracker.report_error("second")

    # Verify
    assert len(caplog.records) == 1
    assert "Too many errors" in caplog.records[0].message


def test_cancellation_message_should_list_recorded_errors():
    # Setup
    tracker = BoundedErrorTracker(max_errors=1)
    tracker.report_error("first")

    # Exercise / Verify
    with pytest.raises(CancelledExecutionError, match=r'''"first".*"second"'''):
        tracker.report_error("second")


def test_report_exception_should_count_towards_the_limit():
    # Setup
    tracker = BoundedErrorTracker(max_errors=1)
    tracker.report_exception(ValueError("first"))

    # Exercise / Verify
    with pytest.raises(CancelledExecutionError, match="Too many errors"):
        tracker.report_exception(ValueError("kaboom"))
