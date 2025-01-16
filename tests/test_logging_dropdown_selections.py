"""Tests for the logging dropdown selections module."""

from unittest.mock import mock_open, patch

import pytest
from fastapi.testclient import TestClient

from src.python_src.util.logging_dropdown_selections import build_logging_table


@pytest.fixture
def mock_csv_data() -> str:
    return (
        "Autosuggestion Name,Other Columns\n"
        "Tinnitus (ringing in ears),data\n"
        "PTSD (post-traumatic stress disorder),data\n"
        "Knee pain,data\n"
    )


def test_first_function(test_client: TestClient, mock_csv_data: str) -> None:
    """Test build_logging_table with mock data."""
    with patch("builtins.open", mock_open(read_data=mock_csv_data)):
        result = build_logging_table("mock_csv_filepath.csv")
        assert result == [
            "tinnitus (ringing in ears)",
            "ptsd (post-traumatic stress disorder)",
            "knee pain",
        ]


def test_second_function(test_client: TestClient) -> None:
    """Test build_logging_table with incomplete rows."""
    incomplete_csv_data = (
        "Autosuggestion Name,Other Columns\n"
        "Tinnitus (ringing in ears),data\n"
        "PTSD (post-traumatic stress disorder)\n"  # missing column
        "Knee pain,data\n"
    )
    with patch("builtins.open", mock_open(read_data=incomplete_csv_data)):
        result = build_logging_table("mock_csv_filepath.csv")
        # Function processes all rows regardless of missing columns
        assert result == [
            "tinnitus (ringing in ears)",
            "ptsd (post-traumatic stress disorder)",
            "knee pain",
        ]


def test_third_function(test_client: TestClient) -> None:
    """Test error handling when file cannot be opened."""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        with pytest.raises(FileNotFoundError):
            build_logging_table("mock_filepath.csv")


def test_fourth_function(test_client: TestClient) -> None:
    """Test build_logging_table with empty file."""
    with patch("builtins.open", mock_open(read_data="Autosuggestion Name,Other Columns\n")):
        result = build_logging_table("mock_filepath.csv")
        assert result == []
