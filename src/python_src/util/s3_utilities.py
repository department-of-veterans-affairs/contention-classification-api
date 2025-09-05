"""
S3 utilities for handling ML model downloads and file verification.

This module provides functionality for:
- Downloading ML models and vectorizers from AWS S3
- SHA-256 hash calculation and verification of files
- Secure file integrity checking with configurable chunk sizes

Functions:
    calculate_file_sha256: Calculate SHA-256 hash of a file
    verify_file_sha256: Verify file SHA-256 against expected value
    download_ml_models_from_s3: Download ML models from S3 with verification
"""

import hashlib
import logging
import os
from typing import Any, Dict, Tuple

import boto3

logger = logging.getLogger(__name__)


def calculate_file_sha256(file_path: str, chunk_size: int) -> str:
    """
    Calculate SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash
        chunk_size: Size of chunks to read from file

    Returns:
        Hexadecimal SHA-256 hash of the file

    Raises:
        OSError: If there's an error reading the file
        IOError: If the file cannot be opened
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except (OSError, IOError) as e:
        logger.error(f"Error calculating SHA-256 for {file_path}: {e}")
        raise


def verify_file_sha256(file_path: str, expected_sha256: str, chunk_size: int) -> bool:
    """
    Verify that a file's SHA-256 matches the expected value.

    Args:
        file_path: Path to the file to verify
        expected_sha256: Expected SHA-256 hash in hexadecimal
        chunk_size: Size of chunks to read from file

    Returns:
        True if the file's SHA-256 matches the expected value, False otherwise
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found for SHA verification: {file_path}")
        return False

    try:
        actual_sha256 = calculate_file_sha256(file_path, chunk_size)
        is_valid = actual_sha256 == expected_sha256

        if is_valid:
            logger.info(f"SHA-256 verification successful for {os.path.basename(file_path)}")
            return True

        _log_verification_failure(file_path, expected_sha256, actual_sha256)
        return False

    except (OSError, IOError) as e:
        _log_verification_error(file_path, str(e))
        return False


def _log_verification_failure(file_path: str, expected_sha256: str, actual_sha256: str) -> None:
    """Log SHA-256 verification failure to monitoring system."""
    log_data = {
        "event": "sha256_verification_failed",
        "file_name": os.path.basename(file_path),
        "file_path": file_path,
        "expected_sha256": expected_sha256,
        "actual_sha256": actual_sha256,
        "error_type": "checksum_mismatch",
        "component": "ml_classifier",
        "severity": "error",
    }
    logger.error("SHA-256 verification failed", extra={"json_data": log_data})


def _log_verification_error(file_path: str, error_message: str) -> None:
    """Log SHA-256 verification error to monitoring system."""
    log_data = {
        "event": "sha256_verification_error",
        "file_name": os.path.basename(file_path),
        "file_path": file_path,
        "error_message": error_message,
        "error_type": "verification_exception",
        "component": "ml_classifier",
        "severity": "error",
    }
    logger.error("SHA-256 verification error", extra={"json_data": log_data})


def download_ml_models_from_s3(model_file: str, vectorizer_file: str, app_config: Dict[str, Any]) -> Tuple[str, str]:
    """
    Download machine learning model files from AWS S3.

    Downloads both the ONNX model file and vectorizer pickle file from S3
    based on the current environment configuration. The function determines
    the appropriate S3 bucket based on the ENV environment variable.

    Args:
        model_file: Local path where the model file should be saved
        vectorizer_file: Local path where the vectorizer file should be saved
        app_config: Application configuration dictionary

    Returns:
        Tuple of (model_file, vectorizer_file) paths

    Environment Variables:
        ENV: Determines which S3 bucket to use ('dev', 'staging', 'prod', 'sandbox').
             Defaults to 'staging' if not set or invalid.

    Raises:
        ValueError: If SHA-256 verification fails and security is enabled
        Exception: If S3 download operations fail

    Example:
        >>> from .app_utilities import app_config
        >>> model_path, vectorizer_path = download_ml_models_from_s3(
        ...     "/tmp/model.onnx", "/tmp/vectorizer.pkl", app_config
        ... )
    """
    # Determine environment and S3 bucket
    env = _get_environment(app_config)
    s3_client = boto3.client("s3")
    bucket = app_config["aws"]["s3"]["buckets"][env]

    # Get verification settings
    verification_config = app_config["ml_classifier"]["integrity_verification"]
    sha_check_enabled = verification_config.get("enabled", False)

    # Get chunk size from ML classifier config
    chunk_size = verification_config.get("hash_config", {}).get("chunk_size_bytes", 4096)

    if sha_check_enabled:
        _log_verification_info(verification_config)

    # Download and verify model file
    _download_and_verify_file(
        s3_client=s3_client,
        bucket=bucket,
        s3_key=app_config["ml_classifier"]["s3_objects"]["model"],
        local_path=model_file,
        expected_sha=_get_expected_sha(verification_config, "model", "ML_MODEL_SHA256"),
        chunk_size=chunk_size,
        sha_check_enabled=sha_check_enabled,
        file_type="model",
    )

    # Download and verify vectorizer file
    _download_and_verify_file(
        s3_client=s3_client,
        bucket=bucket,
        s3_key=app_config["ml_classifier"]["s3_objects"]["vectorizer"],
        local_path=vectorizer_file,
        expected_sha=_get_expected_sha(verification_config, "vectorizer", "ML_VECTORIZER_SHA256"),
        chunk_size=chunk_size,
        sha_check_enabled=sha_check_enabled,
        file_type="vectorizer",
    )

    return model_file, vectorizer_file


def _get_environment(app_config: Dict[str, Any]) -> str:
    """Get and validate the environment setting."""
    env = os.environ.get("ENV")

    # Validate that the environment exists in configuration
    if env is None:
        available_envs = list(app_config["aws"]["s3"]["buckets"].keys())
        logger.error(f"No environment specified (ENV variable not set). Available environments: {available_envs}")
        raise ValueError("No environment specified - ENV environment variable must be set")

    if env not in app_config["aws"]["s3"]["buckets"]:
        available_envs = list(app_config["aws"]["s3"]["buckets"].keys())
        logger.error(f"Environment '{env}' not found in S3 bucket configuration. Available environments: {available_envs}")
        raise ValueError(f"Environment '{env}' not found in S3 bucket configuration")
    return env


def _get_expected_sha(verification_config: Dict[str, Any], file_type: str, env_var: str) -> str:
    """Get expected SHA-256 hash from environment variable or config, with env var taking precedence.

    Returns:
        str: Expected SHA-256 hash if found, empty string otherwise
    """
    # Environment variable takes precedence if set
    env_value = os.environ.get(env_var)
    if env_value:
        return env_value

    # Fall back to config value (if set; empty string otherwise)
    if "expected_checksums" not in verification_config or file_type not in verification_config["expected_checksums"]:
        return ""

    config_value = verification_config["expected_checksums"][file_type]
    return str(config_value) if config_value is not None else ""


def _log_verification_info(verification_config: Dict[str, Any]) -> None:
    """Log verification configuration information."""
    logger.info("SHA-256 verification is enabled for ML model downloads")

    # Only log SHA values if they exist in config
    if "expected_checksums" not in verification_config:
        return

    model_sha = _get_expected_sha(verification_config, "model", "ML_MODEL_SHA256")
    vectorizer_sha = _get_expected_sha(verification_config, "vectorizer", "ML_VECTORIZER_SHA256")

    if model_sha:
        logger.info(f"Expected model SHA-256: {model_sha}")
    if vectorizer_sha:
        logger.info(f"Expected vectorizer SHA-256: {vectorizer_sha}")


def _download_and_verify_file(
    s3_client: Any,
    bucket: str,
    s3_key: str,
    local_path: str,
    expected_sha: str,
    chunk_size: int,
    sha_check_enabled: bool,
    file_type: str,
) -> None:
    """Download a file from S3 and verify its integrity."""
    try:
        logger.info(f"Downloading {file_type} file from S3: {local_path}")
        s3_client.download_file(bucket, s3_key, local_path)

        # Verify SHA-256 if enabled
        if not sha_check_enabled:
            return

        logger.info(f"Verifying SHA-256 of downloaded {file_type} file: {os.path.basename(local_path)}")
        if verify_file_sha256(local_path, expected_sha, chunk_size):
            return

        logger.error(f"{file_type.capitalize()} file SHA-256 verification failed!")

        # Remove the invalid file for security
        if os.path.exists(local_path):
            os.remove(local_path)
            logger.info(f"Removed invalid {file_type} file: {local_path}")

        raise ValueError(f"{file_type.capitalize()} file SHA-256 verification failed - file removed for security")

    except ValueError:
        # Re-raise ValueError from SHA verification failure
        raise
    except Exception as e:
        logger.error(f"Failed to download {file_type} file from S3: {e}")
        raise
