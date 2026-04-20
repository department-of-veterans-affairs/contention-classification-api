"""Tests for the lookup table module."""

from typing import Dict
from unittest.mock import mock_open, patch

import pytest

from src.python_src.util.app_utilities import app_config, diagnostic_code_inits, dropdown_expanded_table_inits
from src.python_src.util.lookup_table import ContentionTextLookupTable, DiagnosticCodeLookupTable

term_columns = app_config["condition_dropdown_table"]["input_key"]
classification_columns = [
    app_config["condition_dropdown_table"]["classification_code"],
    app_config["condition_dropdown_table"]["classification_name"],
    app_config["condition_dropdown_table"]["active_classification"],
]
column_names = ",".join(term_columns + classification_columns)  # add string for mock csv strings


@pytest.fixture
def mock_csv_strings() -> Dict[str, str]:
    return {
        "diagnostic_csv": (
            "DIAGNOSTIC_CODE,CLASSIFICATION_CODE,CLASSIFICATION_TEXT\n7710,6890,Tuberculosis\n6829,9012,Respiratory\n"
        ),
        "contention_csv": (
            f"{column_names}\n"
            "PTSD,,,,,,,,,,,,,,,,,,8989,Mental Disorders,Active\n"
            "Knee pain,,,,,,,,,,,,,,,,,,8997,Knee,Active\n"
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
        f"{column_names}\n"
        "PTSD,,,,,,,,,,,,,,,,,,8989,Mental Disorders,Active\n"
        "PTSD,,,,,,,,,,,,,,,,,,9999,Different Mental Disorder,Active\n"
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


def test_diagnostic_code_lookup_table_file_error() -> None:
    """Test error handling when file cannot be opened."""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        with pytest.raises(FileNotFoundError):
            DiagnosticCodeLookupTable(init_values=diagnostic_code_inits)


def test_contention_text_lookup_table_file_error() -> None:
    """Test error handling when file cannot be opened."""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        with pytest.raises(FileNotFoundError):
            ContentionTextLookupTable(init_values=dropdown_expanded_table_inits)


def test_diagnostic_code_lookup_table_empty_file() -> None:
    """Test DiagnosticCodeLookupTable with empty file."""
    with patch("builtins.open", mock_open(read_data="DIAGNOSTIC_CODE,CLASSIFICATION_CODE,CLASSIFICATION_TEXT\n")):
        table = DiagnosticCodeLookupTable(init_values=diagnostic_code_inits)
        assert table.get("1234")["classification_name"] is None


def test_contention_text_lookup_table_empty_file() -> None:
    """Test ContentionTextLookupTable with empty file."""
    with patch("builtins.open", mock_open(read_data="CONTENTION TEXT,CLASSIFICATION CODE,CLASSIFICATION TEXT\n")):
        table = ContentionTextLookupTable(init_values=dropdown_expanded_table_inits)
        assert table.get("Test")["classification_code"] is None


def test_get_uses_caller_default_value_when_provided(mock_csv_strings: Dict[str, str]) -> None:
    """get() should use the caller-supplied default_value for misses, not the init default."""
    custom_default = {"classification_code": 9999, "classification_name": "Custom Default"}
    with patch("builtins.open", mock_open(read_data=mock_csv_strings["contention_csv"])):
        table = ContentionTextLookupTable(init_values=dropdown_expanded_table_inits)
        result = table.get("nonexistent term", default_value=custom_default)
        assert result == custom_default


def test_get_falls_back_to_init_default_when_none_passed(mock_csv_strings: Dict[str, str]) -> None:
    """get() should fall back to lut_default_value when no default_value is passed."""
    with patch("builtins.open", mock_open(read_data=mock_csv_strings["contention_csv"])):
        table = ContentionTextLookupTable(init_values=dropdown_expanded_table_inits)
        result = table.get("nonexistent term")
        assert result == dropdown_expanded_table_inits.lut_default_value


# Test handling of a column of aggregate_synonyms in the csv
aggregate_synonyms_column = app_config["condition_dropdown_table"]["aggregate_synonyms"]
agg_column_names = ",".join(term_columns + classification_columns + [aggregate_synonyms_column])


def test_aggregate_synonyms_single_token() -> None:
    """A single token in aggregate_synonyms is added as a key mapping to the same classification."""
    csv_data = f"{agg_column_names}\nknee pain,,,,,,,,,,,,,,,,,,8997,Knee,Active,knee ache in mornings\n"
    with patch("builtins.open", mock_open(read_data=csv_data)):
        table = ContentionTextLookupTable(init_values=dropdown_expanded_table_inits)
        assert table.get("knee ache in mornings")["classification_code"] == 8997
        assert table.get("knee ache in mornings")["classification_name"] == "Knee"


def test_aggregate_synonyms_single_token_extra_spaces() -> None:
    """A single token in aggregate_synonyms is trimmed and added as a key mapping to the same classification."""
    csv_data = f"{agg_column_names}\nknee pain,,,,,,,,,,,,,,,,,,8997,Knee,Active,    knee ache in mornings  \n"
    with patch("builtins.open", mock_open(read_data=csv_data)):
        table = ContentionTextLookupTable(init_values=dropdown_expanded_table_inits)
        assert table.get("knee ache in mornings")["classification_code"] == 8997
        assert table.get("knee ache in mornings")["classification_name"] == "Knee"


def test_aggregate_synonyms_multiple_tokens() -> None:
    """Multiple pipe-delimited tokens in aggregate_synonyms are each added as keys."""
    csv_data = f"{agg_column_names}\nknee pain,,,,,,,,,,,,,,,,,,8997,Knee,Active,knee ache|knee soreness|sore knee\n"
    with patch("builtins.open", mock_open(read_data=csv_data)):
        table = ContentionTextLookupTable(init_values=dropdown_expanded_table_inits)
        for synonym in ("knee ache", "knee soreness", "sore knee"):
            assert table.get(synonym)["classification_code"] == 8997


def test_aggregate_synonyms_multiple_tokens_extra_spaces() -> None:
    """Multiple pipe-delimited tokens in aggregate_synonyms are each trimmed and added as keys"""
    csv_data = f"{agg_column_names}\nknee pain,,,,,,,,,,,,,,,,,,8997,Knee,Active,  knee ache  |  knee soreness|  sore knee\n"
    with patch("builtins.open", mock_open(read_data=csv_data)):
        table = ContentionTextLookupTable(init_values=dropdown_expanded_table_inits)
        for synonym in ("knee ache", "knee soreness", "sore knee"):
            assert table.get(synonym)["classification_code"] == 8997


def test_aggregate_synonyms_empty_cell() -> None:
    """An empty aggregate_synonyms cell adds no extra keys beyond the input_key columns."""
    csv_data = f"{agg_column_names}\nknee pain,,,,,,,,,,,,,,,,,,8997,Knee,Active,\n"
    with patch("builtins.open", mock_open(read_data=csv_data)):
        table = ContentionTextLookupTable(init_values=dropdown_expanded_table_inits)
        assert len(table) == 1
        assert table.get("knee pain")["classification_code"] == 8997


def test_aggregate_synonyms_does_not_overwrite_input_key_entry() -> None:
    """A token in aggregate_synonyms that duplicates an input_key entry does not overwrite it."""
    csv_data = (
        f"{agg_column_names}\n"
        # "knee pain" appears as both the primary input_key term and an aggregate synonym
        "knee pain,,,,,,,,,,,,,,,,,,8997,Knee,Active,knee pain|knee ache\n"
    )
    with patch("builtins.open", mock_open(read_data=csv_data)):
        table = ContentionTextLookupTable(init_values=dropdown_expanded_table_inits)
        # "knee pain" should still resolve (not be dropped or duplicated unexpectedly)
        assert table.get("knee pain")["classification_code"] == 8997
        assert table.get("knee ache")["classification_code"] == 8997


def test_aggregate_synonyms_inactive_row_ignored() -> None:
    """aggregate_synonyms tokens from inactive rows are not added to the table."""
    csv_data = f"{agg_column_names}\nknee pain,,,,,,,,,,,,,,,,,,8997,Knee,Inactive,soreness in knee\n"
    with patch("builtins.open", mock_open(read_data=csv_data)):
        table = ContentionTextLookupTable(init_values=dropdown_expanded_table_inits)
        assert len(table) == 0
        assert table.get("soreness in knee")["classification_code"] is None


def test_get_returns_copy_not_alias(mock_csv_strings: Dict[str, str]) -> None:
    """get() should return a copy of the stored mapping dict so callers cannot corrupt
    entries that share the same underlying dict instance (e.g. input_key + aggregate synonyms)."""
    with patch("builtins.open", mock_open(read_data=mock_csv_strings["contention_csv"])):
        table = ContentionTextLookupTable(init_values=dropdown_expanded_table_inits)
        first_result = table.get("Test")
        first_result["classification_code"] = 9999  # mutate the returned copy
        second_result = table.get("Test")
        assert second_result["classification_code"] != 9999, (
            "Mutating the dict returned by get() should not affect the stored mapping"
        )
