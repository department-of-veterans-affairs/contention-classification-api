"""Test SHA-256 verification functionality for ML classifier files."""

import hashlib
import io
import os
import tempfile
from typing import Any
from unittest.mock import patch

from src.python_src.util.app_utilities import app_config
from src.python_src.util.s3_utilities import (
    calculate_file_sha256,
    verify_file_sha256,
)


@patch("src.python_src.util.s3_utilities.open", create=True)
@patch("src.python_src.util.s3_utilities.os.path.exists", return_value=True)
def test_sha_verification_with_expected_config(mock_exists: Any, mock_open: Any) -> None:
    """Test SHA verification configuration and basic functionality."""
    # Verify configuration
    sha_enabled = app_config["ml_classifier"]["integrity_verification"]["enabled"]
    expected_model_sha = app_config["ml_classifier"]["integrity_verification"]["expected_checksums"]["model"]
    expected_vectorizer_sha = app_config["ml_classifier"]["integrity_verification"]["expected_checksums"]["vectorizer"]
    chunk_size = app_config["ml_classifier"]["integrity_verification"]["hash_config"]["chunk_size_bytes"]

    assert sha_enabled is True, "SHA verification should be enabled in configuration"
    assert expected_model_sha is not None, "Expected model SHA should be configured"
    assert expected_vectorizer_sha is not None, "Expected vectorizer SHA should be configured"
    assert chunk_size > 0, "Chunk size should be positive"

    # Mock file content
    mock_content = b"test content"
    mock_open.return_value.__enter__.return_value = io.BytesIO(mock_content)

    # Test verification with dummy hash (should fail)
    result = verify_file_sha256(app_config["ml_classifier"]["files"]["model_filename"], "dummy_hash", chunk_size)
    assert result is False, "SHA verification should fail with incorrect hash"


@patch("src.python_src.util.s3_utilities.open", create=True)
@patch("src.python_src.util.s3_utilities.os.path.exists", return_value=True)
def test_sha_verification_with_wrong_hash(mock_exists: Any, mock_open: Any) -> None:
    """Test that SHA verification properly fails with incorrect hash."""
    chunk_size = app_config["ml_classifier"]["integrity_verification"]["hash_config"]["chunk_size_bytes"]
    wrong_hash = "0000000000000000000000000000000000000000000000000000000000000000"

    # Mock file content
    mock_content = b"test content that won't match the wrong hash"
    mock_open.return_value.__enter__.return_value = io.BytesIO(mock_content)

    # Test both model and vectorizer files
    assert verify_file_sha256(app_config["ml_classifier"]["files"]["model_filename"], wrong_hash, chunk_size) is False
    assert verify_file_sha256(app_config["ml_classifier"]["files"]["vectorizer_filename"], wrong_hash, chunk_size) is False


def test_calculate_file_sha256_with_known_content() -> None:
    """Test SHA-256 calculation with known content."""
    chunk_size = app_config["ml_classifier"]["integrity_verification"]["hash_config"]["chunk_size_bytes"]
    test_content = b"test content for SHA calculation"
    expected_sha = hashlib.sha256(test_content).hexdigest()

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(test_content)
        temp_file.flush()

        try:
            # Test consistency
            sha1 = calculate_file_sha256(temp_file.name, chunk_size)
            sha2 = calculate_file_sha256(temp_file.name, chunk_size)

            assert sha1 == sha2, "SHA calculation should be consistent"
            assert sha1 == expected_sha, f"SHA should match expected value: {expected_sha}"
            assert len(sha1) == 64, "SHA-256 should be 64 characters long"
            assert all(c in "0123456789abcdef" for c in sha1), "SHA-256 should only contain hex characters"
        finally:
            os.unlink(temp_file.name)
