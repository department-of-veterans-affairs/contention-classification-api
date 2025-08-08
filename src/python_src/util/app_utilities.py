"""
This file is used to create shared resources for the application.
Methods
-------
load_config
    Load the configuration file.
read_csv_to_list
    Read a CSV file and return a list of dictionaries.

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

import logging
import os
from typing import Any, Dict, cast

import boto3
from yaml import safe_load

from .expanded_lookup_table import ExpandedLookupTable
from .logging_dropdown_selections import build_logging_table
from .lookup_table import ContentionTextLookupTable, DiagnosticCodeLookupTable
from .lookup_tables_utilities import InitValues
from .ml_classifier import MLClassifier


def load_config(config_file: str) -> Dict[str, Any]:
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


def download_ml_models_from_s3(model_file: str, vectorizer_file: str) -> tuple[str, str]:
    # Get ENV with a default value if not set
    env = os.environ.get("ENV", "staging")  # defaults to 'staging'
    if env not in app_config["ml_classifier"]["aws"]["bucket"]:
        logging.warning(f"Environment '{env}' not found in S3 bucket configuration")
        env = "staging"

    s3_client = boto3.client("s3")
    bucket = app_config["ml_classifier"]["aws"]["bucket"][env]

    try:
        logging.info(f"Downloading model file from S3: {model_file}")
        s3_client.download_file(
            bucket,
            app_config["ml_classifier"]["aws"]["model"],
            model_file,
        )
    except Exception as e:
        logging.error("Failed to download model file from S3: %s", e)

    try:
        logging.info(f"Downloading vectorizer file from S3: {vectorizer_file}")
        s3_client.download_file(
            bucket,
            app_config["ml_classifier"]["aws"]["vectorizer"],
            vectorizer_file,
        )
    except Exception as e:
        logging.error("Failed to download vectorizer file from S3: %s", e)
    return model_file, vectorizer_file


model_directory = os.path.join(os.path.dirname(__file__), app_config["ml_classifier"]["data"]["directory"])
model_file = os.path.join(model_directory, app_config["ml_classifier"]["data"]["model_file"])
vectorizer_file = os.path.join(model_directory, app_config["ml_classifier"]["data"]["vectorizer_file"])

# download all files from S3 if a full set is not already present locally
if not os.path.exists(model_file) or not os.path.exists(vectorizer_file):
    os.makedirs(model_directory, exist_ok=True)
    download_ml_models_from_s3(model_file, vectorizer_file)

ml_classifier = None
if os.path.exists(model_file) and os.path.exists(vectorizer_file):
    ml_classifier = MLClassifier(model_file, vectorizer_file)
