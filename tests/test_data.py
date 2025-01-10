from src.python_src.util.app_utilities import contention_text_csv_filepath, dc_csv_filepath, load_config
from src.python_src.util.expanded_lookup_table import ExpandedLookupTable
from src.python_src.util.lookup_table import (
    ContentionTextLookupTable,
    DiagnosticCodeLookupTable,
)

app_config = load_config("src/python_src/util/app_config.yaml")
default_lut_table = app_config["lut_default_value"]


CONTENTION_DROPDOWN_LUT_SIZE = 1056
DIAGNOSTIC_CODE_LUT_SIZE = 755


def test_build_dropdown_lookup_table():
    lookup_table = ContentionTextLookupTable(
        csv_filepath=contention_text_csv_filepath,
        input_key=app_config["condition_dropdown_table"]["input_key"],
        classification_code=app_config["condition_dropdown_table"]["classification_code"],
        classification_name=app_config["condition_dropdown_table"]["classification_name"],
        lut_default_value=default_lut_table,
    )
    assert len(lookup_table) == CONTENTION_DROPDOWN_LUT_SIZE


def test_build_dc_lut():
    dc_lookup_table = DiagnosticCodeLookupTable(
        csv_filepath=dc_csv_filepath,
        input_key=app_config["diagnostic_code_table"]["input_key"],
        classification_code=app_config["diagnostic_code_table"]["classification_code"],
        classification_name=app_config["diagnostic_code_table"]["classification_name"],
        lut_default_value=default_lut_table,
    )
    assert len(dc_lookup_table) == DIAGNOSTIC_CODE_LUT_SIZE


def test_build_expanded_table():
    expanded = ExpandedLookupTable(
        csv_filepath=contention_text_csv_filepath,
        key_text=app_config["expanded_classifier"]["contention_text"],
        classification_code=app_config["expanded_classifier"]["classification_code"],
        classification_name=app_config["expanded_classifier"]["classification_name"],
        common_words=app_config["common_words"],
        musculoskeletal_lut=app_config["musculoskeletal_lut"],
        lut_default_value=default_lut_table,
    )
    assert len(expanded.contention_text_lookup_table) == 1017
