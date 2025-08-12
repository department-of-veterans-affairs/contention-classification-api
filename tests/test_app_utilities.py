from importlib import reload
from unittest.mock import MagicMock, patch

from src.python_src.util import app_utilities


@patch("src.python_src.util.app_utilities.os.path.exists")
@patch("src.python_src.util.app_utilities.boto3.client")
def test_download_models_from_s3_when_files_missing(mock_boto_client: MagicMock, mock_os_path: MagicMock) -> None:
    """Test that S3 download works correctly when model files are missing locally."""
    mock_s3_client = MagicMock()
    mock_boto_client.return_value = mock_s3_client

    # Mock os.path.exists to return False (files don't exist locally)
    mock_os_path.return_value = False

    reload(app_utilities)

    # Call download method directly
    app_utilities.download_ml_models_from_s3(app_utilities.model_file, app_utilities.vectorizer_file)

    # Verify S3 download was called with correct parameters
    app_config = app_utilities.app_config
    expected_vectorizer_key = app_config["ml_classifier"]["aws"]["vectorizer"]
    expected_model_key = app_config["ml_classifier"]["aws"]["model"]
    expected_bucket = app_config["ml_classifier"]["aws"]["bucket"]

    mock_s3_client.download_file.assert_any_call(expected_bucket, expected_vectorizer_key, app_utilities.vectorizer_file)
    mock_s3_client.download_file.assert_any_call(expected_bucket, expected_model_key, app_utilities.model_file)


@patch("src.python_src.util.ml_classifier.ort.InferenceSession")
@patch("src.python_src.util.ml_classifier.joblib.load")
@patch("src.python_src.util.app_utilities.os.path.exists")
@patch("src.python_src.util.app_utilities.boto3.client")
def test_does_not_download_models_from_s3_when_files_exist(
    mock_boto_client: MagicMock, mock_os_path: MagicMock, mock_joblib: MagicMock, mock_onnx_session: MagicMock
) -> None:
    """Test that S3 download is skipped when model files exist locally."""
    mock_s3_client = MagicMock()
    mock_boto_client.return_value = mock_s3_client

    # Mock os.path.exists to return True (files exist locally)
    mock_os_path.return_value = True

    reload(app_utilities)

    # Verify S3 download was NOT called since files exist locally
    mock_s3_client.download_file.assert_not_called()
    mock_boto_client.assert_not_called()

    # assert that MLClassifier was instantiated
    mock_onnx_session.assert_called_once_with(app_utilities.model_file)
    mock_joblib.assert_called_once_with(app_utilities.vectorizer_file)
    assert app_utilities.ml_classifier is not None


def test_aws_model_key_config_validation() -> None:
    """Test that the model key from config meets expected requirements."""
    app_config = app_utilities.app_config
    model_key = app_config["ml_classifier"]["aws"]["model"]

    assert isinstance(model_key, str), "Model key should be a string"
    assert len(model_key) > 0, "Model key should not be empty"
    assert model_key.endswith(".onnx"), "Model key should end with .onnx extension"
    assert "model" in model_key.lower(), "Model key should contain 'model' in the name"
    assert model_key != app_config["ml_classifier"]["aws"]["vectorizer"], "Model key should be different from vectorizer key"


def test_aws_vectorizer_key_config_validation() -> None:
    """Test that the vectorizer key from config meets expected requirements."""
    app_config = app_utilities.app_config
    vectorizer_key = app_config["ml_classifier"]["aws"]["vectorizer"]

    assert isinstance(vectorizer_key, str), "Vectorizer key should be a string"
    assert len(vectorizer_key) > 0, "Vectorizer key should not be empty"
    assert vectorizer_key.endswith(".pkl"), "Vectorizer key should end with .pkl extension"
    assert "vectorizer" in vectorizer_key.lower(), "Vectorizer key should contain 'vectorizer' in the name"
    assert vectorizer_key != app_config["ml_classifier"]["aws"]["model"], "Vectorizer key should be different from model key"
