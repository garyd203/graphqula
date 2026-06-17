import logging

from graphqula import ErrorTracker, FieldErrorData


def test_report_error_should_record_message_and_return_data():
    # Setup
    tracker = ErrorTracker()

    # Exercise
    returned = tracker.report_error("bad field")

    # Verify
    assert returned == FieldErrorData(message="bad field")
    assert tracker.get_errors() == (FieldErrorData(message="bad field"),)


def test_report_error_should_log_warning_message(caplog):
    # Setup
    caplog.set_level(logging.WARNING)

    tracker = ErrorTracker()

    # Exercise
    tracker.report_error("can't frobnicate the widget")

    # Verify
    assert len(caplog.records) == 1
    assert "can't frobnicate the widget" in caplog.records[0].message


def test_report_exception_should_record_exception_message_and_return_data():
    # Setup
    tracker = ErrorTracker()

    # Exercise
    returned = tracker.report_exception(ValueError("kaboom"))

    # Verify
    assert returned == FieldErrorData(message="kaboom")
    assert tracker.get_errors() == (FieldErrorData(message="kaboom"),)


def test_report_exception_should_log_warning_message(caplog):
    # Setup
    caplog.set_level(logging.WARNING)

    tracker = ErrorTracker()

    # Exercise
    try:
        raise ValueError("can't frobnicate the widget")
    except ValueError as ex:
        tracker.report_exception(ex)

    # Verify
    assert len(caplog.records) == 1
    assert "can't frobnicate the widget" in caplog.records[0].message


def test_should_preserve_error_order():
    # Setup
    tracker = ErrorTracker()

    # Exercise
    tracker.report_error("first")
    tracker.report_error("second")
    tracker.report_exception(RuntimeError("third"))

    # Verify
    assert [e.message for e in tracker.get_errors()] == ["first", "second", "third"]


def test_get_errors_should_return_read_only_copy():
    # Setup
    tracker = ErrorTracker()
    tracker.report_error("only one")

    # Exercise
    initial_errors = tracker.get_errors()

    # Verify
    assert isinstance(initial_errors, tuple)
    assert len(initial_errors) == 1

    tracker.report_error("another")
    assert len(initial_errors) == 1
    assert len(tracker.get_errors()) == 2
