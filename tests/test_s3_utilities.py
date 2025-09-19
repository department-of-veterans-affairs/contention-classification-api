"""Tests for s3_utilities module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.python_src.util.s3_utilities import (
    calculate_file_sha256,
    download_ml_models_from_s3,
    verify_file_sha256,
)


# Get chunk size from app config for tests
def get_chunk_size() -> int:
    """Get chunk size from app configuration."""
    from src.python_src.util.app_utilities import app_config

    return int(app_config["ml_classifier"]["integrity_verification"]["hash_config"]["chunk_size_bytes"])


@patch("src.python_src.util.s3_utilities.verify_file_sha256", return_value=True)
@patch("src.python_src.util.s3_utilities.os.makedirs")
@patch("src.python_src.util.s3_utilities.os.remove")
@patch("src.python_src.util.s3_utilities.os.path.exists")
@patch("src.python_src.util.s3_utilities.boto3.client")
def test_download_ml_models_from_s3_success(
    mock_boto_client: MagicMock,
    mock_os_path: MagicMock,
    mock_os_remove: MagicMock,
    mock_makedirs: MagicMock,
    mock_verify_sha: MagicMock,
) -> None:
    """Test successful S3 download with SHA verification."""
    # Setup S3 client mock
    mock_s3_client = MagicMock()
    mock_boto_client.return_value = mock_s3_client

    # Create temporary file paths
    with (
        tempfile.NamedTemporaryFile(suffix=".onnx", delete=False) as model_temp,
        tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as vectorizer_temp,
    ):
        temp_model_path = model_temp.name
        temp_vectorizer_path = vectorizer_temp.name

    try:
        # Mock file existence check
        mock_os_path.side_effect = lambda path: path in [temp_model_path, temp_vectorizer_path]

        # Mock S3 download
        def mock_download(bucket: str, key: str, filename: str) -> None:
            Path(filename).write_text("mock content")

        mock_s3_client.download_file.side_effect = mock_download

        # Create a mock app_config
        app_config = {
            "aws": {"s3": {"buckets": {"staging": "test-bucket"}}},
            "ml_classifier": {
                "s3_objects": {"model": "model.onnx", "vectorizer": "vectorizer.pkl"},
                "integrity_verification": {
                    "enabled": True,
                    "hash_config": {"chunk_size_bytes": 4096},
                    "expected_checksums": {"model": "test_model_hash", "vectorizer": "test_vectorizer_hash"},
                },
            },
        }

        # Set environment variable for staging
        with patch.dict("os.environ", {"ENV": "staging"}):
            # Execute the function
            result = download_ml_models_from_s3(temp_model_path, temp_vectorizer_path, app_config)

            # Verify S3 download calls
            expected_bucket = app_config["aws"]["s3"]["buckets"]["staging"]  # type: ignore
            expected_vectorizer_key = app_config["ml_classifier"]["s3_objects"]["vectorizer"]  # type: ignore
            expected_model_key = app_config["ml_classifier"]["s3_objects"]["model"]  # type: ignore

            mock_s3_client.download_file.assert_any_call(expected_bucket, expected_vectorizer_key, temp_vectorizer_path)
            mock_s3_client.download_file.assert_any_call(expected_bucket, expected_model_key, temp_model_path)

            # Verify return value
            assert result == (temp_model_path, temp_vectorizer_path)

    finally:
        # Cleanup
        for temp_path in [temp_model_path, temp_vectorizer_path]:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except Exception:
                pass


@patch("src.python_src.util.s3_utilities.boto3.client")
def test_download_ml_models_from_s3_no_environment_variable(mock_boto_client: MagicMock) -> None:
    """Test S3 download with no ENV variable set raises ValueError."""
    mock_s3_client = MagicMock()
    mock_boto_client.return_value = mock_s3_client

    app_config = {
        "aws": {"s3": {"buckets": {"staging": "staging-bucket", "prod": "prod-bucket"}}},
        "ml_classifier": {
            "s3_objects": {"model": "model.onnx", "vectorizer": "vectorizer.pkl"},
            "integrity_verification": {"enabled": False},
        },
    }

    with tempfile.NamedTemporaryFile() as model_temp, tempfile.NamedTemporaryFile() as vectorizer_temp:
        # Clear ENV variable
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="No environment specified - ENV environment variable must be set"):
                download_ml_models_from_s3(model_temp.name, vectorizer_temp.name, app_config)


@patch("src.python_src.util.s3_utilities.boto3.client")
def test_download_ml_models_from_s3_invalid_environment(mock_boto_client: MagicMock) -> None:
    """Test S3 download with invalid environment raises ValueError."""
    mock_s3_client = MagicMock()
    mock_boto_client.return_value = mock_s3_client

    app_config = {
        "aws": {"s3": {"buckets": {"staging": "staging-bucket", "prod": "prod-bucket"}}},
        "ml_classifier": {
            "s3_objects": {"model": "model.onnx", "vectorizer": "vectorizer.pkl"},
            "integrity_verification": {"enabled": False},
        },
    }

    with tempfile.NamedTemporaryFile() as model_temp, tempfile.NamedTemporaryFile() as vectorizer_temp:
        with patch.dict("os.environ", {"ENV": "invalid_env"}):
            with pytest.raises(ValueError, match="Environment 'invalid_env' not found in S3 bucket configuration"):
                download_ml_models_from_s3(model_temp.name, vectorizer_temp.name, app_config)


@patch("src.python_src.util.s3_utilities.verify_file_sha256", return_value=False)
@patch("src.python_src.util.s3_utilities.os.remove")
@patch("src.python_src.util.s3_utilities.os.path.exists", return_value=True)
@patch("src.python_src.util.s3_utilities.boto3.client")
def test_download_ml_models_from_s3_sha_verification_failure(
    mock_boto_client: MagicMock,
    mock_os_exists: MagicMock,
    mock_os_remove: MagicMock,
    mock_verify_sha: MagicMock,
) -> None:
    """Test S3 download with SHA verification failure."""
    mock_s3_client = MagicMock()
    mock_boto_client.return_value = mock_s3_client

    app_config = {
        "aws": {"s3": {"buckets": {"staging": "test-bucket"}}},
        "ml_classifier": {
            "s3_objects": {"model": "model.onnx", "vectorizer": "vectorizer.pkl"},
            "integrity_verification": {
                "enabled": True,
                "hash_config": {"chunk_size_bytes": 4096},
                "expected_checksums": {"model": "expected_model_hash", "vectorizer": "expected_vectorizer_hash"},
            },
        },
    }

    with tempfile.NamedTemporaryFile() as model_temp, tempfile.NamedTemporaryFile() as vectorizer_temp:
        with patch.dict("os.environ", {"ENV": "staging"}):
            with pytest.raises(ValueError, match="Model file SHA-256 verification failed"):
                download_ml_models_from_s3(model_temp.name, vectorizer_temp.name, app_config)

            # Verify file was removed after failed verification
            mock_os_remove.assert_called_with(model_temp.name)


def test_calculate_file_sha256_with_known_content() -> None:
    """Test SHA-256 calculation with known content."""
    import hashlib

    test_content = b"test content for SHA calculation"
    expected_sha = hashlib.sha256(test_content).hexdigest()

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(test_content)
        temp_file.flush()

        try:
            # Test consistency
            sha1 = calculate_file_sha256(temp_file.name, 4096)
            sha2 = calculate_file_sha256(temp_file.name, 4096)

            assert sha1 == sha2, "SHA calculation should be consistent"
            assert sha1 == expected_sha, f"SHA should match expected value: {expected_sha}"
            assert len(sha1) == 64, "SHA-256 should be 64 characters long"
            assert all(c in "0123456789abcdef" for c in sha1), "SHA-256 should only contain hex characters"
        finally:
            Path(temp_file.name).unlink(missing_ok=True)


@patch("src.python_src.util.s3_utilities.os.path.exists", return_value=False)
def test_verify_file_sha256_file_not_found(mock_exists: MagicMock) -> None:
    """Test SHA verification when file doesn't exist."""
    chunk_size = get_chunk_size()
    result = verify_file_sha256("nonexistent_file.txt", "dummy_hash", chunk_size)
    assert result is False


@patch("src.python_src.util.s3_utilities.calculate_file_sha256")
@patch("src.python_src.util.s3_utilities.os.path.exists", return_value=True)
def test_verify_file_sha256_success(mock_exists: MagicMock, mock_calc_sha: MagicMock) -> None:
    """Test successful SHA verification."""
    expected_hash = "abcd1234"
    mock_calc_sha.return_value = expected_hash
    chunk_size = get_chunk_size()

    result = verify_file_sha256("test_file.txt", expected_hash, chunk_size)
    assert result is True


@patch("logging.Logger.error")
@patch("src.python_src.util.s3_utilities.calculate_file_sha256")
@patch("src.python_src.util.s3_utilities.os.path.exists", return_value=True)
def test_verify_file_sha256_error(mock_exists: MagicMock, mock_calc_sha: MagicMock, mock_logger: MagicMock) -> None:
    """Test error in SHA verification."""
    mock_calc_sha.side_effect = OSError()

    result = verify_file_sha256("test_file.txt", "expected_hash", 123)
    mock_logger.assert_called_with(
        "SHA-256 verification error",
        extra={
            "json_data": {
                "event": "sha256_verification_error",
                "file_path": "test_file.txt",
                "error_message": "",
                "error_type": "verification_exception",
                "severity": "error",
            }
        },
    )
    assert result is False


@patch("logging.Logger.error")
@patch("src.python_src.util.s3_utilities.calculate_file_sha256")
@patch("src.python_src.util.s3_utilities.os.path.exists", return_value=True)
def test_verify_file_sha256_failure(mock_exists: MagicMock, mock_calc_sha: MagicMock, mock_logger: MagicMock) -> None:
    """Test failed SHA verification."""
    mock_calc_sha.return_value = "actual_hash"
    chunk_size = get_chunk_size()

    result = verify_file_sha256("test_file.txt", "expected_hash", chunk_size)
    mock_logger.assert_called_with(
        "SHA-256 verification failed",
        extra={
            "json_data": {
                "event": "sha256_verification_failed",
                "file_path": "test_file.txt",
                "expected_sha256": "expected_hash",
                "actual_sha256": "actual_hash",
                "error_type": "checksum_mismatch",
                "severity": "error",
            }
        },
    )
    assert result is False
