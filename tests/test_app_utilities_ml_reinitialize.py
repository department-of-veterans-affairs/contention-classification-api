"""Tests for the ML classifier reinitialization functionality in app_utilities."""

from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from src.python_src.util.app_utilities import reinitialize_ml_classifier


@pytest.fixture
def mock_app_config() -> Dict[str, Any]:
    """Mock app configuration for testing."""
    return {
        "ml_classifier": {
            "files": {"model_filename": "test_model.onnx", "vectorizer_filename": "test_vectorizer.pkl"},
            "storage": {"local_directory": "models/"},
            "s3_objects": {"model": "test_model.onnx", "vectorizer": "test_vectorizer.pkl"},
            "integrity_verification": {"expected_checksums": {"model": "old_model_sha", "vectorizer": "old_vectorizer_sha"}},
        }
    }


@patch("src.python_src.util.app_utilities.app_config")
@patch("src.python_src.util.app_utilities.ml_classifier")
@patch("src.python_src.util.app_utilities.MLClassifier")
@patch("src.python_src.util.app_utilities.os.path.exists")
@patch("src.python_src.util.app_utilities.os.makedirs")
@patch("src.python_src.util.app_utilities.os.remove")
def test_reinitialize_ml_classifier_success(
    mock_remove: MagicMock,
    mock_makedirs: MagicMock,
    mock_exists: MagicMock,
    mock_ml_classifier_class: MagicMock,
    mock_ml_classifier_instance: MagicMock,
    mock_app_config_global: MagicMock,
    mock_app_config: Dict[str, Any],
) -> None:
    """Test successful ML classifier reinitialization."""
    # Setup mocks
    mock_app_config_global.return_value = mock_app_config
    mock_exists.return_value = True
    mock_ml_classifier_instance.version = ("old_model.onnx", "old_vectorizer.pkl")

    # Mock new classifier instance
    new_classifier = MagicMock()
    new_classifier.version = ("new_model.onnx", "new_vectorizer.pkl")
    mock_ml_classifier_class.return_value = new_classifier

    with patch("src.python_src.util.app_utilities.download_ml_models_from_s3") as mock_download:
        mock_download.return_value = None

        # Call the function
        success, message, prev_version, new_version = reinitialize_ml_classifier(
            new_model_filename="new_model.onnx", new_vectorizer_filename="new_vectorizer.pkl", force_download=True
        )

    # Assertions
    assert success is True
    assert "successfully" in message
    assert prev_version["model"] == "old_model.onnx"
    assert new_version["model"] == "new_model.onnx"

    # Verify files were removed due to force_download
    assert mock_remove.call_count == 2  # model and vectorizer files

    # Verify download was called
    mock_download.assert_called_once()

    # Verify new classifier was created
    mock_ml_classifier_class.assert_called_once()


@patch("src.python_src.util.app_utilities.app_config")
@patch("src.python_src.util.app_utilities.ml_classifier")
@patch("src.python_src.util.app_utilities.os.path.exists")
@patch("src.python_src.util.app_utilities.os.makedirs")
def test_reinitialize_ml_classifier_download_failure(
    mock_makedirs: MagicMock,
    mock_exists: MagicMock,
    mock_ml_classifier_instance: MagicMock,
    mock_app_config_global: MagicMock,
    mock_app_config: Dict[str, Any],
) -> None:
    """Test ML classifier reinitialization with download failure."""
    # Setup mocks
    mock_app_config_global.return_value = mock_app_config
    mock_exists.return_value = False  # Files don't exist after "download"
    mock_ml_classifier_instance.version = ("old_model.onnx", "old_vectorizer.pkl")

    with patch("src.python_src.util.app_utilities.download_ml_models_from_s3") as mock_download:
        mock_download.side_effect = Exception("S3 download failed")

        # Call the function
        success, message, prev_version, new_version = reinitialize_ml_classifier(new_model_filename="new_model.onnx")

    # Assertions
    assert success is False
    assert "Failed to download ML models" in message
    assert "S3 download failed" in message
    assert prev_version["model"] == "old_model.onnx"
    assert new_version == {}


@patch("src.python_src.util.app_utilities.app_config")
@patch("src.python_src.util.app_utilities.ml_classifier")
@patch("src.python_src.util.app_utilities.MLClassifier")
@patch("src.python_src.util.app_utilities.os.path.exists")
@patch("src.python_src.util.app_utilities.os.makedirs")
def test_reinitialize_ml_classifier_init_failure(
    mock_makedirs: MagicMock,
    mock_exists: MagicMock,
    mock_ml_classifier_class: MagicMock,
    mock_ml_classifier_instance: MagicMock,
    mock_app_config_global: MagicMock,
    mock_app_config: Dict[str, Any],
) -> None:
    """Test ML classifier reinitialization with classifier init failure."""
    # Setup mocks
    mock_app_config_global.return_value = mock_app_config
    mock_exists.return_value = True  # Files exist
    mock_ml_classifier_instance.version = ("old_model.onnx", "old_vectorizer.pkl")
    mock_ml_classifier_class.side_effect = Exception("Failed to load model")

    with patch("src.python_src.util.app_utilities.download_ml_models_from_s3") as mock_download:
        mock_download.return_value = None

        # Call the function
        success, message, prev_version, new_version = reinitialize_ml_classifier(new_model_filename="new_model.onnx")

    # Assertions
    assert success is False
    assert "Failed to reinitialize ML classifier" in message
    assert "Failed to load model" in message
    assert prev_version["model"] == "old_model.onnx"
    assert new_version == {}


@patch("src.python_src.util.app_utilities.app_config")
@patch("src.python_src.util.app_utilities.ml_classifier")
def test_reinitialize_ml_classifier_no_existing_classifier(
    mock_ml_classifier_instance: MagicMock, mock_app_config_global: MagicMock, mock_app_config: Dict[str, Any]
) -> None:
    """Test ML classifier reinitialization when no existing classifier."""
    # Setup mocks - no existing classifier
    mock_app_config_global.return_value = mock_app_config
    mock_ml_classifier_instance.return_value = None

    with patch("src.python_src.util.app_utilities.download_ml_models_from_s3") as mock_download:
        mock_download.side_effect = Exception("Download failed")

        # Call the function
        success, message, prev_version, new_version = reinitialize_ml_classifier(new_model_filename="new_model.onnx")

    # Assertions
    assert success is False
    assert prev_version == {}  # No previous version since no existing classifier


@patch("src.python_src.util.app_utilities.app_config")
@patch("src.python_src.util.app_utilities.ml_classifier")
@patch("src.python_src.util.app_utilities.MLClassifier")
@patch("src.python_src.util.app_utilities.os.path.exists")
@patch("src.python_src.util.app_utilities.os.makedirs")
def test_reinitialize_ml_classifier_config_update_only(
    mock_makedirs: MagicMock,
    mock_exists: MagicMock,
    mock_ml_classifier_class: MagicMock,
    mock_ml_classifier_instance: MagicMock,
    mock_app_config_global: MagicMock,
    mock_app_config: Dict[str, Any],
) -> None:
    """Test ML classifier reinitialization with only config updates (no new files)."""
    # Setup mocks
    mock_app_config_global.return_value = mock_app_config
    mock_exists.return_value = True
    mock_ml_classifier_instance.version = ("old_model.onnx", "old_vectorizer.pkl")

    # Mock new classifier instance
    new_classifier = MagicMock()
    new_classifier.version = ("new_model.onnx", "new_vectorizer.pkl")
    mock_ml_classifier_class.return_value = new_classifier

    with patch("src.python_src.util.app_utilities.download_ml_models_from_s3") as mock_download:
        mock_download.return_value = None

        # Call the function with SHA update only
        success, message, prev_version, new_version = reinitialize_ml_classifier(new_model_sha256="new_model_sha")

    # Assertions
    assert success is True
    assert prev_version["model"] == "old_model.onnx"
    assert new_version["model"] == "new_model.onnx"

    # Verify config was updated
    assert mock_app_config["ml_classifier"]["integrity_verification"]["expected_checksums"]["model"] == "new_model_sha"


def test_reinitialize_ml_classifier_with_exception() -> None:
    """Test ML classifier reinitialization with unexpected exception."""
    with patch("src.python_src.util.app_utilities.app_config") as mock_config:
        mock_config.side_effect = Exception("Unexpected error")

        # Call the function
        success, message, prev_version, new_version = reinitialize_ml_classifier(new_model_filename="new_model.onnx")

    # Assertions
    assert success is False
    assert "Unexpected error" in message
    assert prev_version == {}
    assert new_version == {}
