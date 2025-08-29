"""Tests for app_utilities module."""

from importlib import reload
from unittest.mock import MagicMock, patch

from src.python_src.util import app_utilities


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


@patch("src.python_src.util.app_utilities.os.remove")
@patch("src.python_src.util.s3_utilities.download_ml_models_from_s3")
@patch("src.python_src.util.ml_classifier.ort.InferenceSession")
@patch("src.python_src.util.ml_classifier.joblib.load")
@patch("src.python_src.util.app_utilities.os.path.exists", return_value=True)
@patch.dict("os.environ", {"DISABLE_SHA_VERIFICATION": "true"}, clear=False)
def test_skip_download_when_files_exist(
    mock_os_path: MagicMock,
    mock_joblib: MagicMock,
    mock_onnx_session: MagicMock,
    mock_download: MagicMock,
    mock_os_remove: MagicMock,
) -> None:
    """Test that S3 download is skipped when model files exist locally."""
    # Reload module to trigger import-time logic
    reload(app_utilities)

    # Verify download was not called since files exist
    mock_download.assert_not_called()

    # Verify ML classifier was initialized
    mock_onnx_session.assert_called_once_with(app_utilities.model_file)
    mock_joblib.assert_called_once_with(app_utilities.vectorizer_file)
    assert app_utilities.ml_classifier is not None
