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

import hashlib
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


def calculate_file_sha256(file_path: str, chunk_size: int = 4096) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logging.error(f"Error calculating SHA-256 for {file_path}: {e}")
        raise


def verify_file_sha256(file_path: str, expected_sha256: str, chunk_size: int = 4096) -> bool:
    """Verify that a file's SHA-256 matches the expected value."""
    if not os.path.exists(file_path):
        logging.error(f"File not found for SHA verification: {file_path}")
        return False

    try:
        actual_sha256 = calculate_file_sha256(file_path, chunk_size)
        is_valid = actual_sha256 == expected_sha256

        if is_valid:
            logging.info(f"SHA-256 verification successful for {os.path.basename(file_path)}")
        else:
            logging.error(f"SHA-256 verification failed for {os.path.basename(file_path)}")
            logging.error(f"Expected: {expected_sha256}")
            logging.error(f"Actual:   {actual_sha256}")

            # Log to DataDog for monitoring and alerting
            try:
                from .logging_utilities import log_as_json

                log_as_json(
                    {
                        "event": "sha256_verification_failed",
                        "file_name": os.path.basename(file_path),
                        "file_path": file_path,
                        "expected_sha256": expected_sha256,
                        "actual_sha256": actual_sha256,
                        "error_type": "checksum_mismatch",
                    }
                )
            except ImportError:
                logging.warning("Could not import log_as_json for DataDog logging")

        return is_valid
    except Exception as e:
        logging.error(f"Error during SHA-256 verification for {file_path}: {e}")

        # Log to DataDog for monitoring and alerting
        try:
            from .logging_utilities import log_as_json

            log_as_json(
                {
                    "event": "sha256_verification_error",
                    "file_name": os.path.basename(file_path),
                    "file_path": file_path,
                    "error_message": str(e),
                    "error_type": "verification_exception",
                }
            )
        except ImportError:
            logging.warning("Could not import log_as_json for DataDog logging")

        return False


def download_ml_models_from_s3(model_file: str, vectorizer_file: str) -> tuple[str, str]:
    """
    Download machine learning model files from AWS S3.

    Downloads both the ONNX model file and vectorizer pickle file from S3
    based on the current environment configuration. The function determines
    the appropriate S3 bucket based on the ENV environment variable.

    Args:
        model_file (str): Local path where the model file should be saved.
        vectorizer_file (str): Local path where the vectorizer file should be saved.

    Returns:
        tuple[str, str]: Tuple of (model_file, vectorizer_file) paths.

    Environment Variables:
        ENV: Determines which S3 bucket to use ('dev', 'staging', 'prod', 'sandbox').
             Defaults to 'staging' if not set or invalid.

    Note:
        - Logs info messages during download process
        - Logs errors if downloads fail but continues execution
        - Falls back to 'staging' environment for unknown ENV values

    Example:
        >>> model_path, vectorizer_path = download_ml_models_from_s3(
        ...     "/tmp/model.onnx", "/tmp/vectorizer.pkl"
        ... )
    """
    # Get ENV with a default value if not set
    env = os.environ.get("ENV", "staging")  # defaults to 'staging'
    if env not in app_config["ml_classifier"]["aws"]["bucket"]:
        logging.warning(f"Environment '{env}' not found in S3 bucket configuration")
        env = "staging"

    s3_client = boto3.client("s3")
    bucket = app_config["ml_classifier"]["aws"]["bucket"][env]

    # Check if SHA verification is enabled
    sha_check_enabled = app_config["ml_classifier"]["verification"]["enable_sha_check"]
    chunk_size = app_config["ml_classifier"]["verification"]["chunk_size"]

    if sha_check_enabled:
        expected_model_sha = app_config["ml_classifier"]["verification"]["expected_sha256"]["model"]
        expected_vectorizer_sha = app_config["ml_classifier"]["verification"]["expected_sha256"]["vectorizer"]

        # Allow environment variables to override config values
        expected_model_sha = os.environ.get("ML_MODEL_SHA256", expected_model_sha)
        expected_vectorizer_sha = os.environ.get("ML_VECTORIZER_SHA256", expected_vectorizer_sha)

        logging.info("SHA-256 verification is enabled for ML model downloads")
        logging.info(f"Expected model SHA-256: {expected_model_sha}")
        logging.info(f"Expected vectorizer SHA-256: {expected_vectorizer_sha}")

    try:
        logging.info(f"Downloading model file from S3: {model_file}")
        s3_client.download_file(
            bucket,
            app_config["ml_classifier"]["aws"]["model"],
            model_file,
        )

        # Verify SHA-256 if enabled
        if sha_check_enabled:
            logging.info(f"Verifying SHA-256 of downloaded model file: {os.path.basename(model_file)}")
            if not verify_file_sha256(model_file, expected_model_sha, chunk_size):
                logging.error("Model file SHA-256 verification failed!")
                # Remove the invalid file
                if os.path.exists(model_file):
                    os.remove(model_file)
                raise Exception("Model file SHA-256 verification failed - file removed for security")

    except Exception as e:
        logging.error("Failed to download model file from S3: %s", e)
        raise

    try:
        logging.info(f"Downloading vectorizer file from S3: {vectorizer_file}")
        s3_client.download_file(
            bucket,
            app_config["ml_classifier"]["aws"]["vectorizer"],
            vectorizer_file,
        )

        # Verify SHA-256 if enabled
        if sha_check_enabled:
            logging.info(f"Verifying SHA-256 of downloaded vectorizer file: {os.path.basename(vectorizer_file)}")
            if not verify_file_sha256(vectorizer_file, expected_vectorizer_sha, chunk_size):
                logging.error("Vectorizer file SHA-256 verification failed!")
                # Remove the invalid file
                if os.path.exists(vectorizer_file):
                    os.remove(vectorizer_file)
                raise Exception("Vectorizer file SHA-256 verification failed - file removed for security")

    except Exception as e:
        logging.error("Failed to download vectorizer file from S3: %s", e)
        raise

    return model_file, vectorizer_file


model_directory = os.path.join(os.path.dirname(__file__), app_config["ml_classifier"]["data"]["directory"])

# Ensure the model directory exists
os.makedirs(model_directory, exist_ok=True)

model_file = os.path.join(model_directory, app_config["ml_classifier"]["data"]["model_file"])
vectorizer_file = os.path.join(model_directory, app_config["ml_classifier"]["data"]["vectorizer_file"])

# Check if we're in a testing environment or CI/CD where AWS credentials might not be available
import_time_download_enabled = os.getenv("DISABLE_ML_DOWNLOAD_AT_IMPORT") != "true"

# Check if SHA verification is enabled
sha_check_enabled = app_config["ml_classifier"]["verification"]["enable_sha_check"]

# Determine if we need to download files
need_download = False

if import_time_download_enabled and (not os.path.exists(model_file) or not os.path.exists(vectorizer_file)):
    need_download = True
    logging.info("Missing model files - will download from S3")
elif import_time_download_enabled and sha_check_enabled:
    # Verify existing files if SHA checking is enabled
    chunk_size = app_config["ml_classifier"]["verification"]["chunk_size"]
    expected_model_sha = app_config["ml_classifier"]["verification"]["expected_sha256"]["model"]
    expected_vectorizer_sha = app_config["ml_classifier"]["verification"]["expected_sha256"]["vectorizer"]

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
elif import_time_download_enabled:
    # Files exist but SHA checking is disabled
    logging.info("Model files exist and SHA-256 verification is disabled - skipping download")

# download all files from S3 if needed
if need_download:
    os.makedirs(model_directory, exist_ok=True)
    try:
        download_ml_models_from_s3(model_file, vectorizer_file)
    except Exception as e:
        logging.warning(f"Failed to download ML models from S3: {e}")
        logging.warning("ML classifier will not be available")

ml_classifier = None
if import_time_download_enabled and os.path.exists(model_file) and os.path.exists(vectorizer_file):
    try:
        ml_classifier = MLClassifier(model_file, vectorizer_file)
        logging.info("ML classifier initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize ML classifier: {e}")
        ml_classifier = None
elif not import_time_download_enabled:
    logging.info("ML classifier initialization disabled at import time")
else:
    logging.warning("ML classifier could not be initialized - model files not available")
