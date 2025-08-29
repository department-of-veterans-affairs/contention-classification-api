"""Tests for the ML classifier configuration endpoint."""

from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.python_src.api import app
from src.python_src.pydantic_models import MLClassifierConfigRequest


@pytest.fixture
def test_client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_config_request() -> Dict[str, Any]:
    """Sample configuration request data."""
    return {
        "model_filename": "new_model_20250829.onnx",
        "vectorizer_filename": "new_vectorizer_20250829.pkl",
        "s3_model_key": "models/new_model_20250829.onnx",
        "s3_vectorizer_key": "models/new_vectorizer_20250829.pkl",
        "force_download": False,
        "expected_model_sha256": "abc123",
        "expected_vectorizer_sha256": "def456",
    }


@patch("src.python_src.api.reinitialize_ml_classifier")
def test_ml_classifier_config_update_success(
    mock_reinitialize: MagicMock, test_client: TestClient, sample_config_request: Dict[str, Any]
) -> None:
    """Test successful ML classifier configuration update."""
    # Mock successful reinitialize
    mock_reinitialize.return_value = (
        True,
        "ML classifier updated successfully",
        {"model": "old_model.onnx", "vectorizer": "old_vectorizer.pkl"},
        {"model": "new_model_20250829.onnx", "vectorizer": "new_vectorizer_20250829.pkl"},
    )

    response = test_client.post("/ml-classifier-config", json=sample_config_request)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "ML classifier updated successfully"
    assert data["previous_version"]["model"] == "old_model.onnx"
    assert data["new_version"]["model"] == "new_model_20250829.onnx"
    assert "model" in data["files_updated"]
    assert "vectorizer" in data["files_updated"]

    # Verify the reinitialize function was called with correct parameters
    mock_reinitialize.assert_called_once_with(
        new_model_filename="new_model_20250829.onnx",
        new_vectorizer_filename="new_vectorizer_20250829.pkl",
        new_s3_model_key="models/new_model_20250829.onnx",
        new_s3_vectorizer_key="models/new_vectorizer_20250829.pkl",
        force_download=False,
        new_model_sha256="abc123",
        new_vectorizer_sha256="def456",
    )


@patch("src.python_src.api.reinitialize_ml_classifier")
def test_ml_classifier_config_update_failure(
    mock_reinitialize: MagicMock, test_client: TestClient, sample_config_request: Dict[str, Any]
) -> None:
    """Test ML classifier configuration update failure."""
    # Mock failed reinitialize
    mock_reinitialize.return_value = (
        False,
        "Failed to download model files",
        {"model": "old_model.onnx", "vectorizer": "old_vectorizer.pkl"},
        {},
    )

    response = test_client.post("/ml-classifier-config", json=sample_config_request)

    assert response.status_code == 500
    data = response.json()
    assert "Failed to download model files" in data["detail"]


def test_ml_classifier_config_no_parameters(test_client: TestClient) -> None:
    """Test ML classifier configuration update with no parameters."""
    empty_request: Dict[str, Any] = {}

    response = test_client.post("/ml-classifier-config", json=empty_request)

    assert response.status_code == 400
    data = response.json()
    assert "At least one configuration parameter must be provided" in data["detail"]


@patch("src.python_src.api.reinitialize_ml_classifier")
def test_ml_classifier_config_force_download_only(mock_reinitialize: MagicMock, test_client: TestClient) -> None:
    """Test ML classifier configuration update with only force_download=True."""
    # Mock successful reinitialize
    mock_reinitialize.return_value = (
        True,
        "ML classifier updated successfully",
        {"model": "old_model.onnx", "vectorizer": "old_vectorizer.pkl"},
        {"model": "old_model.onnx", "vectorizer": "old_vectorizer.pkl"},
    )

    request_data = {"force_download": True}
    response = test_client.post("/ml-classifier-config", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "model" in data["files_updated"]
    assert "vectorizer" in data["files_updated"]

    # Verify the reinitialize function was called with force_download=True
    mock_reinitialize.assert_called_once_with(
        new_model_filename=None,
        new_vectorizer_filename=None,
        new_s3_model_key=None,
        new_s3_vectorizer_key=None,
        force_download=True,
        new_model_sha256=None,
        new_vectorizer_sha256=None,
    )


@patch("src.python_src.api.reinitialize_ml_classifier")
def test_ml_classifier_config_partial_update(mock_reinitialize: MagicMock, test_client: TestClient) -> None:
    """Test ML classifier configuration update with only model filename."""
    # Mock successful reinitialize
    mock_reinitialize.return_value = (
        True,
        "ML classifier updated successfully",
        {"model": "old_model.onnx", "vectorizer": "old_vectorizer.pkl"},
        {"model": "new_model_20250829.onnx", "vectorizer": "old_vectorizer.pkl"},
    )

    request_data = {"model_filename": "new_model_20250829.onnx"}
    response = test_client.post("/ml-classifier-config", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["files_updated"] == ["model"]

    # Verify the reinitialize function was called with only model parameters
    mock_reinitialize.assert_called_once_with(
        new_model_filename="new_model_20250829.onnx",
        new_vectorizer_filename=None,
        new_s3_model_key=None,
        new_s3_vectorizer_key=None,
        force_download=False,
        new_model_sha256=None,
        new_vectorizer_sha256=None,
    )


@patch("src.python_src.api.reinitialize_ml_classifier")
def test_ml_classifier_config_exception_handling(
    mock_reinitialize: MagicMock, test_client: TestClient, sample_config_request: Dict[str, Any]
) -> None:
    """Test ML classifier configuration update with unexpected exception."""
    # Mock exception in reinitialize
    mock_reinitialize.side_effect = Exception("Unexpected error occurred")

    response = test_client.post("/ml-classifier-config", json=sample_config_request)

    assert response.status_code == 500
    data = response.json()
    assert "Unexpected error updating ML classifier configuration" in data["detail"]
    assert "Unexpected error occurred" in data["detail"]


def test_ml_classifier_config_request_validation() -> None:
    """Test MLClassifierConfigRequest pydantic model validation."""
    # Test valid request
    valid_data = {"model_filename": "test_model.onnx", "force_download": True}
    request = MLClassifierConfigRequest(**valid_data)
    assert request.model_filename == "test_model.onnx"
    assert request.force_download is True
    assert request.vectorizer_filename is None

    # Test empty request (should be valid)
    empty_request = MLClassifierConfigRequest()
    assert empty_request.model_filename is None
    assert empty_request.force_download is False
