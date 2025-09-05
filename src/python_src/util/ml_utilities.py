"""
Machine Learning utilities for contention classification.

This module handles ML classifier initialization, model file management,
and download operations for the machine learning classifier.

Functions
---------
load_ml_classifier
    Initialize and return an ML classifier instance with proper model verification

Shared Resources
----------------
ml_classifier
    Machine learning classifier instance for model predictions
"""

import logging
import os
from typing import Any, Dict, Optional

from .ml_classifier import MLClassifier
from .s3_utilities import download_ml_models_from_s3, verify_file_sha256


def get_model_file_paths(app_config: Dict[str, Any]) -> tuple[str, str]:
    """
    Get the file paths for model and vectorizer files.

    Args:
        app_config (Dict[str, Any]): Application configuration dictionary.

    Returns:
        tuple[str, str]: Tuple of (model_file_path, vectorizer_file_path)
    """
    model_directory = os.path.join(os.path.dirname(__file__), app_config["ml_classifier"]["storage"]["local_directory"])
    model_file = os.path.join(model_directory, app_config["ml_classifier"]["files"]["model_filename"])
    vectorizer_file = os.path.join(model_directory, app_config["ml_classifier"]["files"]["vectorizer_filename"])
    return model_file, vectorizer_file


def load_ml_classifier(app_config: Dict[str, Any]) -> Optional[MLClassifier]:
    """
    Load and initialize the ML classifier with proper model verification.

    This function handles the complete ML classifier initialization process including:
    - Model directory creation
    - File existence checks
    - SHA-256 verification (if enabled)
    - S3 download when needed
    - Classifier initialization

    Args:
        app_config (Dict[str, Any]): Application configuration dictionary containing
                                   ML classifier settings, file paths, and verification options.

    Returns:
        Optional[MLClassifier]: Initialized ML classifier instance if successful,
                              None if initialization fails.

    Note:
        SHA verification can be disabled via the DISABLE_SHA_VERIFICATION environment
        variable for development purposes.
    """
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

    # Initialize ML classifier
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

    return ml_classifier
