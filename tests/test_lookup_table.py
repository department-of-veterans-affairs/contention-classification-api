"""Tests for the lookup table module."""

from src.python_src.util.lookup_table import (
    ContentionTextLookupTable,
    DiagnosticCodeLookupTable,
)
from tests.conftest import patch, pytest


def test_diagnostic_code_lookup_table(common_diagnostic_codes, mock_file_open):
    """Test DiagnosticCodeLookupTable with mock data."""
    mock_data = "DIAGNOSTIC_CODE,CLASSIFICATION_CODE,CLASSIFICATION_TEXT\n7710,6890,Tuberculosis\n6829,9012,Respiratory\n"
    with patch("builtins.open", mock_file_open(read_data=mock_data)):
        table = DiagnosticCodeLookupTable()
        assert table.get(7710)["classification_name"] == "Tuberculosis"
        assert table.get(6829)["classification_name"] == "Respiratory"
        assert table.get(9999)["classification_name"] is None


def test_contention_text_lookup_table(mock_file_open):
    """Test ContentionTextLookupTable with mock data."""
    mock_data = "CONTENTION TEXT,CLASSIFICATION CODE,CLASSIFICATION TEXT\nPTSD,8989,Mental Disorders\nKnee pain,8997,Knee\n"
    with patch("builtins.open", mock_file_open(read_data=mock_data)):
        table = ContentionTextLookupTable()
        assert table.get("PTSD")["classification_code"] == 8989
        assert table.get("Knee pain")["classification_code"] == 8997
        assert table.get("Unknown")["classification_code"] is None


def test_diagnostic_code_lookup_table_file_error():
    """Test error handling when file cannot be opened."""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        with pytest.raises(FileNotFoundError):
            DiagnosticCodeLookupTable()


def test_contention_text_lookup_table_file_error():
    """Test error handling when file cannot be opened."""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        with pytest.raises(FileNotFoundError):
            ContentionTextLookupTable()


def test_diagnostic_code_lookup_table_empty_file(mock_file_open):
    """Test DiagnosticCodeLookupTable with empty file."""
    with patch("builtins.open", mock_file_open(read_data="DIAGNOSTIC_CODE,CLASSIFICATION_CODE,CLASSIFICATION_TEXT\n")):
        table = DiagnosticCodeLookupTable()
        assert table.get(1234)["classification_name"] is None


def test_contention_text_lookup_table_empty_file(mock_file_open):
    """Test ContentionTextLookupTable with empty file."""
    with patch("builtins.open", mock_file_open(read_data="CONTENTION TEXT,CLASSIFICATION CODE,CLASSIFICATION TEXT\n")):
        table = ContentionTextLookupTable()
        assert table.get("Test")["classification_code"] is None
