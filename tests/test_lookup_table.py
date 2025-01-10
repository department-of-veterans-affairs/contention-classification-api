"""Tests for the lookup table module."""

from typing import Any, Dict, Union

from src.python_src.util.lookup_table import (
    ContentionTextLookupTable,
    DiagnosticCodeLookupTable,
)
from tests.conftest import patch, pytest


def test_diagnostic_code_lookup_table(
    common_diagnostic_codes: Dict[str, Dict[str, Union[int, str]]], mock_file_open: Any, mock_csv_strings: Dict[str, str]
) -> None:
    """Test DiagnosticCodeLookupTable with mock data."""
    with patch("builtins.open", mock_file_open(read_data=mock_csv_strings["diagnostic_csv"])):
        table = DiagnosticCodeLookupTable()
        assert table.get(7710)["classification_name"] == "Tuberculosis"
        assert table.get(6829)["classification_name"] == "Respiratory"
        assert table.get(9999)["classification_name"] is None


def test_diagnostic_code_lookup_table_duplicate_codes(mock_file_open: Any) -> None:
    """Test how DiagnosticCodeLookupTable handles duplicate codes."""
    duplicate_csv = (
        "DIAGNOSTIC_CODE,CLASSIFICATION_CODE,CLASSIFICATION_TEXT\n7710,6890,Tuberculosis\n7710,7777,Conflicting Tuberculosis\n"
    )
    with patch("builtins.open", mock_file_open(read_data=duplicate_csv)):
        table = DiagnosticCodeLookupTable()
        # Last entry should win
        entry = table.get(7710)
        assert entry["classification_code"] == 7777
        assert entry["classification_name"] == "Conflicting Tuberculosis"


def test_contention_text_lookup_table_duplicate_entries(mock_file_open: Any) -> None:
    """Test how ContentionTextLookupTable handles duplicate entries."""
    duplicate_csv = (
        "CONTENTION TEXT,CLASSIFICATION CODE,CLASSIFICATION TEXT\n"
        "PTSD,8989,Mental Disorders\n"
        "PTSD,9999,Different Mental Disorder\n"
    )
    with patch("builtins.open", mock_file_open(read_data=duplicate_csv)):
        table = ContentionTextLookupTable()
        # Last entry should win
        entry = table.get("PTSD")
        assert entry["classification_code"] == 9999
        assert entry["classification_name"] == "Different Mental Disorder"


def test_contention_text_lookup_table(mock_file_open: Any, mock_csv_strings: Dict[str, str]) -> None:
    """Test ContentionTextLookupTable with mock data."""
    with patch("builtins.open", mock_file_open(read_data=mock_csv_strings["contention_csv"])):
        table = ContentionTextLookupTable()
        assert table.get("PTSD")["classification_code"] == 8989
        assert table.get("Knee pain")["classification_code"] == 8997
        assert table.get("Unknown")["classification_code"] is None


def test_diagnostic_code_lookup_table_file_error() -> None:
    """Test error handling when file cannot be opened."""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        with pytest.raises(FileNotFoundError):
            DiagnosticCodeLookupTable()


def test_contention_text_lookup_table_file_error() -> None:
    """Test error handling when file cannot be opened."""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        with pytest.raises(FileNotFoundError):
            ContentionTextLookupTable()


def test_diagnostic_code_lookup_table_empty_file(mock_file_open: Any) -> None:
    """Test DiagnosticCodeLookupTable with empty file."""
    with patch("builtins.open", mock_file_open(read_data="DIAGNOSTIC_CODE,CLASSIFICATION_CODE,CLASSIFICATION_TEXT\n")):
        table = DiagnosticCodeLookupTable()
        assert table.get(1234)["classification_name"] is None


def test_contention_text_lookup_table_empty_file(mock_file_open: Any) -> None:
    """Test ContentionTextLookupTable with empty file."""
    with patch("builtins.open", mock_file_open(read_data="CONTENTION TEXT,CLASSIFICATION CODE,CLASSIFICATION TEXT\n")):
        table = ContentionTextLookupTable()
        assert table.get("Test")["classification_code"] is None
