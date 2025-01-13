"""
This file is used to create shared resources for the application.
Methods
-------
load_config
    Load the configuration file.

Shared Resources
----------------
dc_lookup_table
    Class used to look up diagnostic codes and map to classifications
dropdown_lookup_table
    Class to use to look up contention text values and map to classifications
expanded_lookup_table
    Class to use in the expanded lookup method
dropdown_values
    List of autosuggestions
"""

import os

import yaml

from .expanded_lookup_table import ExpandedLookupTable
from .logging_dropdown_selections import build_logging_table
from .lookup_table import ContentionTextLookupTable, DiagnosticCodeLookupTable


def load_config(config_file):
    with open(config_file, "r") as f:
        data = yaml.safe_load(f)
    return data


# build the lookup tables after loading the config yaml
app_config = load_config(os.path.join(os.path.dirname(__file__), "app_config.yaml"))

default_lut_table = app_config["lut_default_value"]

dc_table_name = (
    f"{app_config['diagnostic_code_table']['filename']} {app_config['diagnostic_code_table']['version_number']}.csv"
)
dc_csv_filepath = os.path.join(os.path.dirname(__file__), "data", "dc_lookup_table", dc_table_name)

dc_lookup_table = DiagnosticCodeLookupTable(
    csv_filepath=dc_csv_filepath,
    input_key=app_config["diagnostic_code_table"]["input_key"],
    classification_code=app_config["diagnostic_code_table"]["classification_code"],
    classification_name=app_config["diagnostic_code_table"]["classification_name"],
    lut_default_value=default_lut_table,
)

contention_lut_csv_filename = (
    f"{app_config['condition_dropdown_table']['filename']} {app_config['condition_dropdown_table']['version_number']}.csv"
)

contention_text_csv_filepath = os.path.join(
    os.path.dirname(__file__),
    "data",
    "condition_dropdown_lookup_table",
    contention_lut_csv_filename,
)
dropdown_lookup_table = ContentionTextLookupTable(
    csv_filepath=contention_text_csv_filepath,
    input_key=app_config["condition_dropdown_table"]["input_key"],
    classification_code=app_config["condition_dropdown_table"]["classification_code"],
    classification_name=app_config["condition_dropdown_table"]["classification_name"],
    lut_default_value=default_lut_table,
)


expanded_lookup_table = ExpandedLookupTable(
    csv_filepath=contention_text_csv_filepath,
    key_text=app_config["expanded_classifier"]["contention_text"],
    classification_code=app_config["expanded_classifier"]["classification_code"],
    classification_name=app_config["expanded_classifier"]["classification_name"],
    common_words=app_config["common_words"],
    musculoskeletal_lut=app_config["musculoskeletal_lut"],
    lut_default_value=default_lut_table,
)

autosuggestions_path = os.path.join(
    os.path.dirname(__file__),
    "data",
    "condition_dropdown_coverage",
    f"{app_config['autosuggestion_table']['filename']} {app_config['autosuggestion_table']['version_number']} Flat.csv",
)

dropdown_values = build_logging_table(autosuggestions_path)
