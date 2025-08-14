#!/usr/bin/env python3
"""
Test script to verify SHA-256 checking functionality for ML classifier files.
"""

import logging
import os

from src.python_src.util.app_utilities import (
    app_config,
    calculate_file_sha256,
    model_file,
    vectorizer_file,
    verify_file_sha256,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def test_sha_verification() -> None:
    """Test the SHA verification functionality."""
    # Check configuration
    sha_enabled = app_config["ml_classifier"]["verification"]["enable_sha_check"]
    assert sha_enabled is True, "SHA verification should be enabled in configuration"

    # Get expected SHA values
    expected_model_sha = app_config["ml_classifier"]["verification"]["expected_sha256"]["model"]
    expected_vectorizer_sha = app_config["ml_classifier"]["verification"]["expected_sha256"]["vectorizer"]
    chunk_size = app_config["ml_classifier"]["verification"]["chunk_size"]

    assert expected_model_sha is not None, "Expected model SHA should be configured"
    assert expected_vectorizer_sha is not None, "Expected vectorizer SHA should be configured"
    assert chunk_size > 0, "Chunk size should be positive"

    # Test model file
    assert os.path.exists(model_file), f"Model file should exist: {model_file}"
    actual_model_sha = calculate_file_sha256(model_file, chunk_size)
    assert actual_model_sha == expected_model_sha, (
        f"Model SHA mismatch. Expected: {expected_model_sha}, Actual: {actual_model_sha}"
    )

    model_valid = verify_file_sha256(model_file, expected_model_sha, chunk_size)
    assert model_valid is True, "Model file SHA verification should pass"

    # Test vectorizer file
    assert os.path.exists(vectorizer_file), f"Vectorizer file should exist: {vectorizer_file}"
    actual_vectorizer_sha = calculate_file_sha256(vectorizer_file, chunk_size)
    assert actual_vectorizer_sha == expected_vectorizer_sha, (
        f"Vectorizer SHA mismatch. Expected: {expected_vectorizer_sha}, Actual: {actual_vectorizer_sha}"
    )

    vectorizer_valid = verify_file_sha256(vectorizer_file, expected_vectorizer_sha, chunk_size)
    assert vectorizer_valid is True, "Vectorizer file SHA verification should pass"


def test_sha_verification_with_wrong_hash() -> None:
    """Test that SHA verification properly fails with incorrect hash."""
    chunk_size = app_config["ml_classifier"]["verification"]["chunk_size"]

    # Test with a known wrong hash
    wrong_hash = "0000000000000000000000000000000000000000000000000000000000000000"

    if os.path.exists(model_file):
        model_valid = verify_file_sha256(model_file, wrong_hash, chunk_size)
        assert model_valid is False, "SHA verification should fail with wrong hash"

    if os.path.exists(vectorizer_file):
        vectorizer_valid = verify_file_sha256(vectorizer_file, wrong_hash, chunk_size)
        assert vectorizer_valid is False, "SHA verification should fail with wrong hash"


def test_calculate_file_sha256() -> None:
    """Test the SHA-256 calculation function."""
    chunk_size = app_config["ml_classifier"]["verification"]["chunk_size"]

    if os.path.exists(model_file):
        sha1 = calculate_file_sha256(model_file, chunk_size)
        sha2 = calculate_file_sha256(model_file, chunk_size)
        assert sha1 == sha2, "SHA calculation should be consistent"
        assert len(sha1) == 64, "SHA-256 should be 64 characters long"
        assert all(c in "0123456789abcdef" for c in sha1), "SHA-256 should only contain hex characters"
