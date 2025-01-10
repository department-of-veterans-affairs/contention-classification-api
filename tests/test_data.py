from src.python_src.util.expanded_lookup_config import FILE_READ_HELPER
from src.python_src.util.expanded_lookup_table import ExpandedLookupTable
from src.python_src.util.lookup_table import (
    ContentionTextLookupTable,
    DiagnosticCodeLookupTable,
)

CONTENTION_DROPDOWN_LUT_SIZE = 1056
DIAGNOSTIC_CODE_LUT_SIZE = 755


def test_build_dropdown_lookup_table() -> None:
    lookup_table = ContentionTextLookupTable()
    assert len(lookup_table) == CONTENTION_DROPDOWN_LUT_SIZE


def test_build_dc_lut() -> None:
    dc_lookup_table = DiagnosticCodeLookupTable()
    assert len(dc_lookup_table) == DIAGNOSTIC_CODE_LUT_SIZE


def test_build_expanded_table() -> None:
    expanded = ExpandedLookupTable(
        FILE_READ_HELPER["contention_text"],
        FILE_READ_HELPER["classification_code"],
        FILE_READ_HELPER["classification_name"],
    )
    assert len(expanded.contention_text_lookup_table) == 1017
