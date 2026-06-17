import pytest

from graphqula.error_handler import FailFastErrorHandler, CancelledExecutionError


def test_report_error_should_raise_custom_error():
    # Setup
    handler = FailFastErrorHandler()

    # Exercise / Verify
    with pytest.raises(CancelledExecutionError, match="boom"):
        handler.report_error("boom")


def test_report_exception_should_re_raise_original_exception_when_it_has_no_stack_trace():
    # Setup
    handler = FailFastErrorHandler()
    original = ValueError("original failure")

    # Exercise / Verify
    with pytest.raises(ValueError, match="original failure") as exc_info:
        handler.report_exception(original)

    assert exc_info.value is original


def test_report_exception_should_re_raise_original_exception_when_inside_exception_handler():
    # Setup
    handler = FailFastErrorHandler()
    original = ValueError("original failure")

    def fail_badly():
        raise original

    # Exercise / Verify
    with pytest.raises(ValueError, match="original failure") as exc_info:
        try:
            fail_badly()
        except ValueError as ex:
            handler.report_exception(ex)

    # Verify
    assert exc_info.value is original
    assert (
        exc_info.traceback[-1].name == "fail_badly"
    ), "Last entry in the stack trace should be the function where it was originally raised"
    assert (
        exc_info.traceback[-2].name
        == "test_report_exception_should_re_raise_original_exception_when_inside_exception_handler"
    ), "Second last entry in the stack trace should be the funciton where it was caught, in this case"
    assert (
        exc_info.traceback[-3].name == "report_exception"
    ), "Entry above the function where the exception where it was caught should be report_exception itself."


def test_report_exception_should_re_raise_original_exception_when_caught_and_reported_outside_exception_handler():
    # Setup
    handler = FailFastErrorHandler()
    original = ValueError("original failure")

    def fail_badly():
        raise original

    # Exercise / Verify
    with pytest.raises(ValueError, match="original failure") as exc_info:
        cached_ex = None
        try:
            fail_badly()
        except ValueError as ex:
            cached_ex = ex

        assert cached_ex is not None
        handler.report_exception(cached_ex)

    # Verify
    assert exc_info.value is original
    assert (
        exc_info.traceback[-1].name == "fail_badly"
    ), "Last entry in the stack trace should be the function where it was originally raised"
    assert (
        exc_info.traceback[-2].name
        == "test_report_exception_should_re_raise_original_exception_when_caught_and_reported_outside_exception_handler"
    ), "Second last entry in the stack trace should be the funciton where it was caught, in this case"
    assert (
        exc_info.traceback[-3].name == "report_exception"
    ), "Entry above the function where the exception where it was caught should be report_exception itself."
