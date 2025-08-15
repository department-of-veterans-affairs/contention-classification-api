"""Tests for app_utilities module."""

import tempfile
from importlib import reload
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.util import app_utilities


@patch("src.util.app_utilities.verify_file_sha256", return_value=True)
@patch("src.util.app_utilities.os.makedirs")
@patch("src.util.app_utilities.os.remove")
@patch("src.util.app_utilities.os.path.exists")
@patch("src.util.app_utilities.boto3.client")
def test_download_models_when_files_missing(
    mock_boto_client: MagicMock,
    mock_os_path: MagicMock,
    mock_os_remove: MagicMock,
    mock_makedirs: MagicMock,
    mock_verify_sha: MagicMock,
) -> None:
    """Test S3 download when model files are missing locally."""
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

        # Execute the function
        result = app_utilities.download_ml_models_from_s3(temp_model_path, temp_vectorizer_path)

        # Verify S3 download calls
        app_config = app_utilities.app_config
        expected_bucket = app_config["aws"]["s3"]["buckets"]["staging"]
        expected_vectorizer_key = app_config["ml_classifier"]["s3_objects"]["vectorizer"]
        expected_model_key = app_config["ml_classifier"]["s3_objects"]["model"]

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


@patch("src.util.app_utilities.os.remove")
@patch.dict(
    "src.util.app_utilities.app_config",
    {"ml_classifier": {"verification": {"enable_sha_check": False}}},
    clear=False,
)
@patch("src.util.app_utilities.download_ml_models_from_s3")
@patch("src.util.ml_classifier.ort.InferenceSession")
@patch("src.util.ml_classifier.joblib.load")
@patch("src.util.app_utilities.os.path.exists", return_value=True)
@patch("src.util.app_utilities.boto3.client")
@patch.dict("os.environ", {"DISABLE_ML_DOWNLOAD_AT_IMPORT": "false"}, clear=False)
def test_skip_download_when_files_exist(
    mock_boto_client: MagicMock,
    mock_os_path: MagicMock,
    mock_joblib: MagicMock,
    mock_onnx_session: MagicMock,
    mock_download: MagicMock,
    mock_os_remove: MagicMock,
) -> None:
    """Test that S3 download is skipped when model files exist locally."""
    mock_s3_client = MagicMock()
    mock_boto_client.return_value = mock_s3_client

    # Reload module to trigger import-time logic
    reload(app_utilities)

    # Verify download was not called since files exist
    mock_download.assert_not_called()

    # Verify ML classifier was initialized
    mock_onnx_session.assert_called_once_with(app_utilities.model_file)
    mock_joblib.assert_called_once_with(app_utilities.vectorizer_file)
    assert app_utilities.ml_classifier is not None


def test_model_key_config() -> None:
    """Test that the model key configuration meets requirements."""
    app_config = app_utilities.app_config
    model_key = app_config["ml_classifier"]["s3_objects"]["model"]
    vectorizer_key = app_config["ml_classifier"]["s3_objects"]["vectorizer"]

    assert isinstance(model_key, str), "Model key should be a string"
    assert len(model_key) > 0, "Model key should not be empty"
    assert model_key.endswith(".onnx"), "Model key should end with .onnx extension"
    assert "model" in model_key.lower(), "Model key should contain 'model' in the name"
    assert model_key != vectorizer_key, "Model key should be different from vectorizer key"


def test_vectorizer_key_config() -> None:
    """Test that the vectorizer key configuration meets requirements."""
    app_config = app_utilities.app_config
    vectorizer_key = app_config["ml_classifier"]["s3_objects"]["vectorizer"]
    model_key = app_config["ml_classifier"]["s3_objects"]["model"]

    assert isinstance(vectorizer_key, str), "Vectorizer key should be a string"
    assert len(vectorizer_key) > 0, "Vectorizer key should not be empty"
    assert vectorizer_key.endswith(".pkl"), "Vectorizer key should end with .pkl extension"
    assert "vectorizer" in vectorizer_key.lower(), "Vectorizer key should contain 'vectorizer' in the name"
    assert vectorizer_key != model_key, "Vectorizer key should be different from model key"
