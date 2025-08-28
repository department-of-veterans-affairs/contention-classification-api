"""Tests for the sanitizer module."""

from src.util.sanitizer import sanitize_log


def test_sanitize_log_string() -> None:
    """Test sanitize_log with string inputs."""
    assert sanitize_log("test") == "test"
    assert sanitize_log("test\n") == "test"
    assert sanitize_log("test\r\n") == "test"
    assert sanitize_log("test\ntest") == "testtest"
    assert sanitize_log("test\r\ntest") == "testtest"


def test_sanitize_log_boolean() -> None:
    """Test sanitize_log with boolean inputs."""
    assert sanitize_log(True) is True
    assert sanitize_log(False) is False
    assert sanitize_log("True\n") == "True"
    assert sanitize_log("False\r\n") == "False"


def test_sanitize_log_integer() -> None:
    """Test sanitize_log with integer inputs."""
    assert sanitize_log(123) == 123
    assert sanitize_log("123\n") == "123"
    assert sanitize_log("123\r\n") == "123"


def test_sanitize_log_none() -> None:
    """Test sanitize_log with None input."""
    assert sanitize_log(None) == "None"


def test_sanitize_log_special_chars() -> None:
    """Test sanitize_log with special characters."""
    assert sanitize_log("test\ttest") == "test\ttest"
    assert sanitize_log("test\vtest") == "test\vtest"
    assert sanitize_log("test\ftest") == "test\ftest"
