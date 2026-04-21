"""Tests for the data module."""

import os

import pytest

from src.python_src.util.app_utilities import diagnostic_code_inits, load_config
from src.python_src.util.expanded_lookup_table import ExpandedLookupTable
from src.python_src.util.lookup_table import (
    ContentionTextLookupTable,
    DiagnosticCodeLookupTable,
)
from src.python_src.util.lookup_tables_utilities import InitValues

app_config = load_config("src/python_src/util/app_config.yaml")
default_lut_table = app_config["lut_default_value"]

DIAGNOSTIC_CODE_LUT_SIZE = 755

CONTENTION_DROPDOWN_LUT_SIZES = {
    "v0.2": 1502,
    "v0.3": 1746,
}

EXPANDED_LOOKUP_TABLE_SIZES = {
    "v0.2": 1071,
    "v0.3": 1269,
}

MASTER_TAXONOMY_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "python_src", "util", "data", "master_taxonomy")


def _make_dropdown_inits(version: str) -> InitValues:
    filename = app_config["condition_dropdown_table"]["filename"]
    csv_path = os.path.join(MASTER_TAXONOMY_DIR, f"{filename} - {version}.csv")
    return InitValues(
        csv_filepath=csv_path,
        input_key=app_config["condition_dropdown_table"]["input_key"],
        classification_code=app_config["condition_dropdown_table"]["classification_code"],
        classification_name=app_config["condition_dropdown_table"]["classification_name"],
        active_selection=app_config["condition_dropdown_table"]["active_classification"],
        lut_default_value=default_lut_table,
        aggregate_synonyms=app_config["condition_dropdown_table"]["aggregate_synonyms"],
    )


def test_build_dc_lut() -> None:
    dc_lookup_table = DiagnosticCodeLookupTable(diagnostic_code_inits)
    assert len(dc_lookup_table) == DIAGNOSTIC_CODE_LUT_SIZE


@pytest.mark.parametrize("version", ["v0.2", "v0.3"])
def test_build_dropdown_lookup_table(version: str) -> None:
    inits = _make_dropdown_inits(version)
    lookup_table = ContentionTextLookupTable(inits)
    assert len(lookup_table) == CONTENTION_DROPDOWN_LUT_SIZES[version]


@pytest.mark.parametrize("version", ["v0.2", "v0.3"])
def test_build_expanded_table(version: str) -> None:
    inits = _make_dropdown_inits(version)
    expanded = ExpandedLookupTable(
        init_values=inits,
        common_words=app_config["common_words"],
        musculoskeletal_lut=app_config["musculoskeletal_lut"],
    )
    assert len(expanded.contention_text_lookup_table) == EXPANDED_LOOKUP_TABLE_SIZES[version]


def test_lookup_table_v03_aggregate_synonyms() -> None:
    """'trench foot' and 'leg sciatica' are aggregate synonym added in v0.3 of the dropdown table."""
    inits = _make_dropdown_inits("v0.3")
    lookup_table = ContentionTextLookupTable(inits)
    expected_matches = ["trench foot", "leg sciatica"]
    for query in expected_matches:
        result = lookup_table.get(query)
        assert result["classification_code"] is not None, f"'{query}' should be found in v0.3 dropdown table"
