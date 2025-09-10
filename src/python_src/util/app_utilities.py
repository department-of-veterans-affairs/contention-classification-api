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
ml_classifier
    Machine learning classifier instance for model predictions

Note:
    S3-related functions have been moved to s3_utilities.py module.
"""

import os
from typing import Any, Dict, cast

from yaml import safe_load

from .expanded_lookup_table import ExpandedLookupTable
from .logging_dropdown_selections import build_logging_table
from .lookup_table import ContentionTextLookupTable, DiagnosticCodeLookupTable
from .lookup_tables_utilities import InitValues
from .ml_utilities import load_ml_classifier


def load_config(config_file: str) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Reads and parses a YAML configuration file into a Python dictionary.

    Args:
        config_file (str): Path to the YAML configuration file.

    Returns:
        Dict[str, Any]: Dictionary containing the parsed configuration data.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If the YAML file is malformed or cannot be parsed.

    Example:
        >>> config = load_config("app_config.yaml")
        >>> print(config["lut_default_value"])
        'Other'
    """
    with open(config_file, "r") as f:
        return cast(Dict[str, Any], safe_load(f))


# build the lookup tables after loading the config yaml
app_config = load_config(os.path.join(os.path.dirname(__file__), "app_config.yaml"))

default_lut_table = app_config["lut_default_value"]

dc_table_name = (
    f"{app_config['diagnostic_code_table']['filename']} {app_config['diagnostic_code_table']['version_number']}.csv"
)
dc_csv_filepath = os.path.join(os.path.dirname(__file__), "data", "dc_lookup_table", dc_table_name)

diagnostic_code_inits = InitValues(
    csv_filepath=dc_csv_filepath,
    input_key=app_config["diagnostic_code_table"]["input_key"],
    classification_code=app_config["diagnostic_code_table"]["classification_code"],
    classification_name=app_config["diagnostic_code_table"]["classification_name"],
    active_selection=None,
    lut_default_value=default_lut_table,
)


dc_lookup_table = DiagnosticCodeLookupTable(init_values=diagnostic_code_inits)

contention_lut_csv_filename = (
    f"{app_config['condition_dropdown_table']['filename']} - {app_config['condition_dropdown_table']['version_number']}.csv"
)

contention_text_csv_filepath = os.path.join(
    os.path.dirname(__file__),
    "data",
    "master_taxonomy",
    contention_lut_csv_filename,
)

dropdown_expanded_table_inits = InitValues(
    csv_filepath=contention_text_csv_filepath,
    input_key=app_config["condition_dropdown_table"]["input_key"],
    classification_code=app_config["condition_dropdown_table"]["classification_code"],
    classification_name=app_config["condition_dropdown_table"]["classification_name"],
    active_selection=app_config["condition_dropdown_table"]["active_classification"],
    lut_default_value=default_lut_table,
)
dropdown_lookup_table = ContentionTextLookupTable(dropdown_expanded_table_inits)


expanded_lookup_table = ExpandedLookupTable(
    init_values=dropdown_expanded_table_inits,
    common_words=app_config["common_words"],
    musculoskeletal_lut=app_config["musculoskeletal_lut"],
)

autosuggestions_path = os.path.join(
    os.path.dirname(__file__),
    "data",
    "master_taxonomy",
    f"{app_config['autosuggestion_table']['filename']} - {app_config['autosuggestion_table']['version_number']}.csv",
)

dropdown_values = build_logging_table(
    autosuggestions_path,
    app_config["autosuggestion_table"]["autocomplete_terms"],
    app_config["autosuggestion_table"]["active_autocomplete"],
)

# Initialize ML classifier using the ml_utilities module
ml_classifier = load_ml_classifier(app_config)
