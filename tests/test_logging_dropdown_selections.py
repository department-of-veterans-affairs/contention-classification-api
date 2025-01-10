"""Tests for the logging dropdown selections module."""

from typing import Any
from unittest.mock import patch

from src.python_src.util.logging_dropdown_selections import (
    build_logging_table,
    build_logging_table_v0_1,
)
from tests.conftest import pytest


@pytest.fixture
def mock_csv_data() -> str:
    """Mock CSV data for testing."""
    return (
        "Autosuggestion Name,Other Columns\n"
        "Tinnitus (ringing in ears),data\n"
        "PTSD (post-traumatic stress disorder),data\n"
        "Knee pain,data\n"
    )


@pytest.fixture
def mock_csv_data_v0_1() -> str:
    """Mock CSV data for testing v0.1 format."""
    return (
        "Conditions list terms, organized by base term and variations\n"
        "Base Term,UI Term 1,UI Term 2,UI Term 3,UI Term 4,UI Term 5,UI Term 6\n"
        "tinnitus,Tinnitus,Ringing in ears,,,,\n"
        "ptsd,PTSD,Post-traumatic stress disorder,,,,\n"
        "knee,Knee pain,Knee condition,,,,\n"
    )


def test_build_logging_table(mock_csv_data: str, mock_file_open: Any) -> None:
    """Test build_logging_table with mock data."""
    with patch("builtins.open", mock_file_open(read_data=mock_csv_data)):
        result = build_logging_table()
        assert result == [
            "tinnitus (ringing in ears)",
            "ptsd (post-traumatic stress disorder)",
            "knee pain",
        ]


def test_build_logging_table_incomplete_rows(mock_file_open: Any) -> None:
    """Test build_logging_table with incomplete rows."""
    incomplete_csv_data = (
        "Autosuggestion Name,Other Columns\n"
        "Tinnitus (ringing in ears),data\n"
        "PTSD (post-traumatic stress disorder)\n"  # missing column
        "Knee pain,data\n"
    )
    with patch("builtins.open", mock_file_open(read_data=incomplete_csv_data)):
        result = build_logging_table()
        # Function processes all rows regardless of missing columns
        assert result == [
            "tinnitus (ringing in ears)",
            "ptsd (post-traumatic stress disorder)",
            "knee pain",
        ]


def test_build_logging_table_v0_1_incomplete_rows(mock_file_open: Any) -> None:
    """Test build_logging_table_v0_1 with incomplete rows."""
    incomplete_csv_data = (
        "Conditions list terms, organized by base term and variations\n"
        "Base Term,UI Term 1,UI Term 2,UI Term 3,UI Term 4,UI Term 5,UI Term 6\n"
        "tinnitus,Tinnitus,Ringing in ears,,,,\n"
        "ptsd\n"  # incomplete row
        "knee,Knee pain,Knee condition,,,,\n"
    )
    with patch("builtins.open", mock_file_open(read_data=incomplete_csv_data)):
        result = build_logging_table_v0_1()
        # Function skips incomplete rows and processes valid ones
        assert result == [
            "tinnitus",
            "ringing in ears",
            "knee pain",
            "knee condition",
        ]


def test_build_logging_table_v0_1(mock_csv_data_v0_1: str, mock_file_open: Any) -> None:
    """Test build_logging_table_v0_1 with mock data."""
    with patch("builtins.open", mock_file_open(read_data=mock_csv_data_v0_1)):
        result = build_logging_table_v0_1()
        assert result == [
            "tinnitus",
            "ringing in ears",
            "ptsd",
            "post-traumatic stress disorder",
            "knee pain",
            "knee condition",
        ]


def test_build_logging_table_file_error() -> None:
    """Test error handling when file cannot be opened."""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        with pytest.raises(FileNotFoundError):
            build_logging_table()


def test_build_logging_table_v0_1_file_error() -> None:
    """Test error handling when file cannot be opened for v0.1."""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        with pytest.raises(FileNotFoundError):
            build_logging_table_v0_1()


def test_build_logging_table_empty_file(mock_file_open: Any) -> None:
    """Test build_logging_table with empty file."""
    with patch("builtins.open", mock_file_open(read_data="Autosuggestion Name,Other Columns\n")):
        result = build_logging_table()
        assert result == []


def test_build_logging_table_v0_1_empty_file(mock_file_open: Any) -> None:
    """Test build_logging_table_v0_1 with empty file."""
    empty_data = (
        "Conditions list terms, organized by base term and variations\n"
        "Base Term,UI Term 1,UI Term 2,UI Term 3,UI Term 4,UI Term 5,UI Term 6\n"
    )
    with patch("builtins.open", mock_file_open(read_data=empty_data)):
        result = build_logging_table_v0_1()
        assert result == []
