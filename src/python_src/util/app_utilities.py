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

import logging
import os
from typing import Any, Dict, cast

from yaml import safe_load

from .expanded_lookup_table import ExpandedLookupTable
from .logging_dropdown_selections import build_logging_table
from .lookup_table import ContentionTextLookupTable, DiagnosticCodeLookupTable
from .lookup_tables_utilities import InitValues
from .ml_classifier import MLClassifier
from .s3_utilities import download_ml_models_from_s3, verify_file_sha256


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

# Load ML classifier configuration

model_directory = os.path.join(os.path.dirname(__file__), app_config["ml_classifier"]["storage"]["local_directory"])

# Ensure the model directory exists
os.makedirs(model_directory, exist_ok=True)

model_file = os.path.join(model_directory, app_config["ml_classifier"]["files"]["model_filename"])
vectorizer_file = os.path.join(model_directory, app_config["ml_classifier"]["files"]["vectorizer_filename"])

# Check if SHA verification is enabled
sha_check_enabled = app_config["ml_classifier"]["integrity_verification"]["enabled"]
# Allow disabling SHA verification via environment variable for development
sha_check_enabled = sha_check_enabled and os.getenv("DISABLE_SHA_VERIFICATION") != "true"

# Determine if we need to download files
need_download = False

if not os.path.exists(model_file) or not os.path.exists(vectorizer_file):
    need_download = True
    logging.info("Missing model files - will download from S3")
elif sha_check_enabled:
    # Verify existing files if SHA checking is enabled
    chunk_size = app_config["ml_classifier"]["integrity_verification"]["hash_config"]["chunk_size_bytes"]
    expected_model_sha = app_config["ml_classifier"]["integrity_verification"]["expected_checksums"]["model"]
    expected_vectorizer_sha = app_config["ml_classifier"]["integrity_verification"]["expected_checksums"]["vectorizer"]

    # Allow environment variables to override config values
    expected_model_sha = os.environ.get("ML_MODEL_SHA256", expected_model_sha)
    expected_vectorizer_sha = os.environ.get("ML_VECTORIZER_SHA256", expected_vectorizer_sha)

    logging.info("Verifying SHA-256 of existing model files")
    logging.info(f"Expected model SHA-256: {expected_model_sha}")
    logging.info(f"Expected vectorizer SHA-256: {expected_vectorizer_sha}")

    model_valid = verify_file_sha256(model_file, expected_model_sha, chunk_size)
    vectorizer_valid = verify_file_sha256(vectorizer_file, expected_vectorizer_sha, chunk_size)

    if not model_valid or not vectorizer_valid:
        logging.warning("Existing model files failed SHA-256 verification - will re-download from S3")
        # Remove invalid files
        if not model_valid and os.path.exists(model_file):
            os.remove(model_file)
        if not vectorizer_valid and os.path.exists(vectorizer_file):
            os.remove(vectorizer_file)
        need_download = True
    else:
        logging.info("All existing model files passed SHA-256 verification - skipping download")
else:
    # Files exist and SHA checking is disabled
    logging.info("Model files exist and SHA-256 verification is disabled - skipping download")

# download all files from S3 if needed
if need_download:
    os.makedirs(model_directory, exist_ok=True)
    try:
        download_ml_models_from_s3(model_file, vectorizer_file, app_config)
        logging.info("Successfully downloaded ML models from S3")
    except ValueError as e:
        # ValueError indicates SHA verification failure - don't use fallback for security
        logging.error(f"ML model download failed due to verification error: {e}")
        logging.error("ML classifier will not be available - security verification failed")
    except Exception as e:
        logging.error(f"Failed to download ML models from S3: {e}")
        logging.error("ML classifier will not be available - download failed")

ml_classifier = None
if os.path.exists(model_file) and os.path.exists(vectorizer_file):
    try:
        ml_classifier = MLClassifier(model_file, vectorizer_file)
        logging.info("ML classifier initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize ML classifier: {e}")
        ml_classifier = None
else:
    logging.warning("ML classifier could not be initialized - model files not available")
