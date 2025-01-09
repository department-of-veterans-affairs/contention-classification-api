from src.python_src.util.app_utilities import load_config
from src.python_src.util.expanded_lookup_table import ExpandedLookupTable
from src.python_src.util.lookup_table import (
    ContentionTextLookupTable,
    DiagnosticCodeLookupTable,
)

app_config = load_config("src/python_src/util/app_config.yaml")
CONTENTION_DROPDOWN_LUT_SIZE = 1056
DIAGNOSTIC_CODE_LUT_SIZE = 755


def test_build_dropdown_lookup_table():
    lookup_table = ContentionTextLookupTable()
    assert len(lookup_table) == CONTENTION_DROPDOWN_LUT_SIZE


def test_build_dc_lut():
    dc_lookup_table = DiagnosticCodeLookupTable()
    assert len(dc_lookup_table) == DIAGNOSTIC_CODE_LUT_SIZE


def test_build_expanded_table():
    expanded = ExpandedLookupTable(
        key_text=app_config["expanded_classifier"]["contention_text"],
        classification_code=app_config["expanded_classifier"]["classification_code"],
        classification_name=app_config["expanded_classifier"]["classification_name"],
    )
    assert len(expanded.contention_text_lookup_table) == 1017
