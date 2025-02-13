"""Tests for the data module."""

from src.python_src.util.app_utilities import diagnostic_code_inits, dropdown_expanded_table_inits, load_config
from src.python_src.util.expanded_lookup_table import ExpandedLookupTable
from src.python_src.util.lookup_table import (
    ContentionTextLookupTable,
    DiagnosticCodeLookupTable,
)

app_config = load_config("src/python_src/util/app_config.yaml")
default_lut_table = app_config["lut_default_value"]


CONTENTION_DROPDOWN_LUT_SIZE = 1056
DIAGNOSTIC_CODE_LUT_SIZE = 755


def test_build_dropdown_lookup_table() -> None:
    lookup_table = ContentionTextLookupTable(dropdown_expanded_table_inits)
    assert len(lookup_table) == CONTENTION_DROPDOWN_LUT_SIZE


def test_build_dc_lut() -> None:
    dc_lookup_table = DiagnosticCodeLookupTable(diagnostic_code_inits)
    assert len(dc_lookup_table) == DIAGNOSTIC_CODE_LUT_SIZE


def test_build_expanded_table() -> None:
    expanded = ExpandedLookupTable(
        init_values=dropdown_expanded_table_inits,
        common_words=app_config["common_words"],
        musculoskeletal_lut=app_config["musculoskeletal_lut"],
    )
    assert len(expanded.contention_text_lookup_table) == 1037
