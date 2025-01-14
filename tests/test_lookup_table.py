"""Tests for the lookup table module."""

from typing import Dict, Any, List
from unittest.mock import patch, mock_open, Mock

import pytest
from fastapi.testclient import TestClient

from src.python_src.util.lookup_table import ContentionTextLookupTable, DiagnosticCodeLookupTable
from src.python_src.util.expanded_lookup_table import ExpandedLookupTable
from src.python_src.util.app_utilities import diagnostic_code_inits, dropdown_expanded_table_inits

@pytest.fixture
def mock_csv_strings() -> Dict[str, str]:
    return {
        "diagnostic_csv": (
            "DIAGNOSTIC_CODE,CLASSIFICATION_CODE,CLASSIFICATION_TEXT\n7710,6890,Tuberculosis\n6829,9012,Respiratory\n"
        ),
        "contention_csv": (
            "CONTENTION TEXT,CLASSIFICATION CODE,CLASSIFICATION TEXT\nPTSD,8989,Mental Disorders\nKnee pain,8997,Knee\n"
        ),
        "logging_csv": (
            "Autosuggestion Name,Other Columns\nTinnitus (ringing in ears),data\nPTSD (post-traumatic stress disorder),data\n"
        ),
        "logging_v0_1_csv": (
            "Conditions list terms, organized by base term and variations\n"
            "Base Term,UI Term 1,UI Term 2,UI Term 3,UI Term 4,UI Term 5,UI Term 6\n"
            "tinnitus,Tinnitus,Ringing in ears,,,,\n"
        ),
    }

def test_diagnostic_code_lookup_table_duplicate_codes() -> None:
    """Test how DiagnosticCodeLookupTable handles duplicate codes."""
    duplicate_csv = (
        "DIAGNOSTIC_CODE,CLASSIFICATION_CODE,CLASSIFICATION_TEXT\n7710,6890,Tuberculosis\n7710,7777,Conflicting Tuberculosis\n"
    )
    with patch("builtins.open", mock_open(read_data=duplicate_csv)):
        table = DiagnosticCodeLookupTable(init_values=diagnostic_code_inits)
        # Last entry should win
        entry = table.get("7710")
        assert entry["classification_code"] == 7777
        assert entry["classification_name"] == "Conflicting Tuberculosis"

def test_contention_text_lookup_table_duplicate_entries() -> None:
    """Test how ContentionTextLookupTable handles duplicate entries."""
    duplicate_csv = (
        "CONTENTION TEXT,CLASSIFICATION CODE,CLASSIFICATION TEXT\n"
        "PTSD,8989,Mental Disorders\n"
        "PTSD,9999,Different Mental Disorder\n"
    )
    with patch("builtins.open", mock_open(read_data=duplicate_csv)):
        table = ContentionTextLookupTable(init_values=dropdown_expanded_table_inits)
        # Last entry should win
        entry = table.get("PTSD")
        assert entry["classification_code"] == 9999
        assert entry["classification_name"] == "Different Mental Disorder"

def test_contention_text_lookup_table(mock_csv_strings: Dict[str, str]) -> None:
    """Test ContentionTextLookupTable with mock data."""
    with patch("builtins.open", mock_open(read_data=mock_csv_strings["contention_csv"])):
        table = ContentionTextLookupTable(init_values=dropdown_expanded_table_inits)
        assert table.get("PTSD")["classification_code"] == 8989
        assert table.get("Knee pain")["classification_code"] == 8997
        assert table.get("Unknown")["classification_code"] is None
