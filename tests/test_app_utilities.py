from importlib import reload
from unittest.mock import MagicMock, mock_open, patch

import pytest
from botocore.exceptions import ClientError, NoCredentialsError
from yaml import YAMLError

from src.python_src.util import app_utilities


def test_load_config() -> None:
    """Test that load_config successfully loads and parses a YAML file."""
    mock_yaml_content = """
    test_key: test_value
    nested:
        key: nested_value
    list_key:
        - item1
        - item2
    """
    with patch("builtins.open", mock_open(read_data=mock_yaml_content)):
        result = app_utilities.load_config("test_config.yaml")

    expected = {"test_key": "test_value", "nested": {"key": "nested_value"}, "list_key": ["item1", "item2"]}
    assert result == expected


def test_load_config_file_error() -> None:
    """Test that load_config raises appropriate error when file cannot be read."""
    with patch("builtins.open", side_effect=FileNotFoundError("Config file not found")):
        with pytest.raises(FileNotFoundError):
            app_utilities.load_config("nonexistent_config.yaml")


def test_load_config_yaml_parse_error() -> None:
    """Test that load_config raises appropriate error for invalid YAML."""
    invalid_yaml = "invalid: yaml: content: ["
    with patch("builtins.open", mock_open(read_data=invalid_yaml)):
        with pytest.raises(YAMLError):  # YAML parsing error
            app_utilities.load_config("invalid_config.yaml")


@patch("src.python_src.util.app_utilities.os.environ.get")
@patch("src.python_src.util.app_utilities.boto3.client")
def test_download_ml_models_from_s3_with_environment_staging(mock_boto_client: MagicMock, mock_env_get: MagicMock) -> None:
    """Test download with staging environment."""
    mock_s3_client = MagicMock()
    mock_boto_client.return_value = mock_s3_client
    mock_env_get.return_value = "staging"

    model_file = "/tmp/test_model.onnx"
    vectorizer_file = "/tmp/test_vectorizer.pkl"

    result = app_utilities.download_ml_models_from_s3(model_file, vectorizer_file)

    # Verify staging bucket is used
    expected_bucket = app_utilities.app_config["ml_classifier"]["aws"]["bucket"]["staging"]
    expected_model_key = app_utilities.app_config["ml_classifier"]["aws"]["model"]
    expected_vectorizer_key = app_utilities.app_config["ml_classifier"]["aws"]["vectorizer"]

    mock_s3_client.download_file.assert_any_call(expected_bucket, expected_model_key, model_file)
    mock_s3_client.download_file.assert_any_call(expected_bucket, expected_vectorizer_key, vectorizer_file)
    assert result == (model_file, vectorizer_file)


@patch("src.python_src.util.app_utilities.os.environ.get")
@patch("src.python_src.util.app_utilities.boto3.client")
def test_download_ml_models_from_s3_with_environment_prod(mock_boto_client: MagicMock, mock_env_get: MagicMock) -> None:
    """Test download with prod environment."""
    mock_s3_client = MagicMock()
    mock_boto_client.return_value = mock_s3_client
    mock_env_get.return_value = "prod"

    model_file = "/tmp/test_model.onnx"
    vectorizer_file = "/tmp/test_vectorizer.pkl"

    result = app_utilities.download_ml_models_from_s3(model_file, vectorizer_file)

    # Verify prod bucket is used
    expected_bucket = app_utilities.app_config["ml_classifier"]["aws"]["bucket"]["prod"]
    expected_model_key = app_utilities.app_config["ml_classifier"]["aws"]["model"]
    expected_vectorizer_key = app_utilities.app_config["ml_classifier"]["aws"]["vectorizer"]

    mock_s3_client.download_file.assert_any_call(expected_bucket, expected_model_key, model_file)
    mock_s3_client.download_file.assert_any_call(expected_bucket, expected_vectorizer_key, vectorizer_file)
    assert result == (model_file, vectorizer_file)


@patch("src.python_src.util.app_utilities.os.environ.get")
@patch("src.python_src.util.app_utilities.logging")
@patch("src.python_src.util.app_utilities.boto3.client")
def test_download_ml_models_from_s3_invalid_environment_fallback(
    mock_boto_client: MagicMock, mock_logging: MagicMock, mock_env_get: MagicMock
) -> None:
    """Test download with invalid environment falls back to staging."""
    mock_s3_client = MagicMock()
    mock_boto_client.return_value = mock_s3_client
    mock_env_get.return_value = "invalid_env"

    model_file = "/tmp/test_model.onnx"
    vectorizer_file = "/tmp/test_vectorizer.pkl"

    result = app_utilities.download_ml_models_from_s3(model_file, vectorizer_file)

    # Verify warning was logged
    mock_logging.warning.assert_called_with("Environment 'invalid_env' not found in S3 bucket configuration")

    # Verify staging bucket is used as fallback
    expected_bucket = app_utilities.app_config["ml_classifier"]["aws"]["bucket"]["staging"]
    expected_model_key = app_utilities.app_config["ml_classifier"]["aws"]["model"]
    expected_vectorizer_key = app_utilities.app_config["ml_classifier"]["aws"]["vectorizer"]

    mock_s3_client.download_file.assert_any_call(expected_bucket, expected_model_key, model_file)
    mock_s3_client.download_file.assert_any_call(expected_bucket, expected_vectorizer_key, vectorizer_file)
    assert result == (model_file, vectorizer_file)


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
    expected_bucket = app_config["ml_classifier"]["aws"]["bucket"]["staging"]  # default env

    mock_s3_client.download_file.assert_any_call(expected_bucket, expected_vectorizer_key, app_utilities.vectorizer_file)
    mock_s3_client.download_file.assert_any_call(expected_bucket, expected_model_key, app_utilities.model_file)


@patch("src.python_src.util.app_utilities.boto3.client")
def test_download_ml_models_from_s3_success(mock_boto_client: MagicMock) -> None:
    """Test successful download of ML models from S3."""
    mock_s3_client = MagicMock()
    mock_boto_client.return_value = mock_s3_client

    model_file = "/tmp/test_model.onnx"
    vectorizer_file = "/tmp/test_vectorizer.pkl"

    # Call the function
    result = app_utilities.download_ml_models_from_s3(model_file, vectorizer_file)

    # Verify return values
    assert result == (model_file, vectorizer_file)

    # Verify S3 client was created and called correctly
    mock_boto_client.assert_called_once_with("s3")
    assert mock_s3_client.download_file.call_count == 2

    # Check the calls were made with correct parameters
    app_config = app_utilities.app_config
    expected_bucket = app_config["ml_classifier"]["aws"]["bucket"]["staging"]  # default env
    expected_model_key = app_config["ml_classifier"]["aws"]["model"]
    expected_vectorizer_key = app_config["ml_classifier"]["aws"]["vectorizer"]

    mock_s3_client.download_file.assert_any_call(expected_bucket, expected_model_key, model_file)
    mock_s3_client.download_file.assert_any_call(expected_bucket, expected_vectorizer_key, vectorizer_file)


@patch("src.python_src.util.app_utilities.logging")
@patch("src.python_src.util.app_utilities.boto3.client")
def test_download_ml_models_from_s3_model_download_error(mock_boto_client: MagicMock, mock_logging: MagicMock) -> None:
    """Test handling of model download error from S3."""
    mock_s3_client = MagicMock()
    mock_boto_client.return_value = mock_s3_client

    # Mock S3 client to raise an exception for model download
    mock_s3_client.download_file.side_effect = [
        ClientError({"Error": {"Code": "NoSuchKey"}}, "download_file"),  # Model download fails
        None,  # Vectorizer download succeeds
    ]

    model_file = "/tmp/test_model.onnx"
    vectorizer_file = "/tmp/test_vectorizer.pkl"

    # Call the function
    result = app_utilities.download_ml_models_from_s3(model_file, vectorizer_file)

    # Verify return values are still returned
    assert result == (model_file, vectorizer_file)

    # Verify error was logged
    mock_logging.error.assert_called_once()
    error_call = mock_logging.error.call_args[0]
    assert "Failed to download model file from S3" in error_call[0]


@patch("src.python_src.util.app_utilities.logging")
@patch("src.python_src.util.app_utilities.boto3.client")
def test_download_ml_models_from_s3_vectorizer_download_error(mock_boto_client: MagicMock, mock_logging: MagicMock) -> None:
    """Test handling of vectorizer download error from S3."""
    mock_s3_client = MagicMock()
    mock_boto_client.return_value = mock_s3_client

    # Mock S3 client to raise an exception for vectorizer download
    mock_s3_client.download_file.side_effect = [
        None,  # Model download succeeds
        ClientError({"Error": {"Code": "NoSuchKey"}}, "download_file"),  # Vectorizer download fails
    ]

    model_file = "/tmp/test_model.onnx"
    vectorizer_file = "/tmp/test_vectorizer.pkl"

    # Call the function
    result = app_utilities.download_ml_models_from_s3(model_file, vectorizer_file)

    # Verify return values are still returned
    assert result == (model_file, vectorizer_file)

    # Verify error was logged
    mock_logging.error.assert_called_once()
    error_call = mock_logging.error.call_args[0]
    assert "Failed to download vectorizer file from S3" in error_call[0]


@patch("src.python_src.util.app_utilities.logging")
@patch("src.python_src.util.app_utilities.boto3.client")
def test_download_ml_models_from_s3_both_downloads_fail(mock_boto_client: MagicMock, mock_logging: MagicMock) -> None:
    """Test handling when both model and vectorizer downloads fail."""
    mock_s3_client = MagicMock()
    mock_boto_client.return_value = mock_s3_client

    # Mock S3 client to raise exceptions for both downloads
    mock_s3_client.download_file.side_effect = [
        ClientError({"Error": {"Code": "NoSuchKey"}}, "download_file"),  # Model download fails
        ClientError({"Error": {"Code": "AccessDenied"}}, "download_file"),  # Vectorizer download fails
    ]

    model_file = "/tmp/test_model.onnx"
    vectorizer_file = "/tmp/test_vectorizer.pkl"

    # Call the function
    result = app_utilities.download_ml_models_from_s3(model_file, vectorizer_file)

    # Verify return values are still returned
    assert result == (model_file, vectorizer_file)

    # Verify both errors were logged
    assert mock_logging.error.call_count == 2
    error_calls = [call[0][0] for call in mock_logging.error.call_args_list]
    assert any("Failed to download model file from S3" in call for call in error_calls)
    assert any("Failed to download vectorizer file from S3" in call for call in error_calls)


@patch("src.python_src.util.app_utilities.logging")
@patch("src.python_src.util.app_utilities.boto3.client")
def test_download_ml_models_from_s3_no_credentials(mock_boto_client: MagicMock, mock_logging: MagicMock) -> None:
    """Test handling of AWS credentials error."""
    # Mock boto3.client to raise NoCredentialsError
    mock_boto_client.side_effect = NoCredentialsError()

    model_file = "/tmp/test_model.onnx"
    vectorizer_file = "/tmp/test_vectorizer.pkl"

    # Call the function and expect it to raise the exception
    with pytest.raises(NoCredentialsError):
        app_utilities.download_ml_models_from_s3(model_file, vectorizer_file)


@patch("src.python_src.util.app_utilities.logging")
@patch("src.python_src.util.app_utilities.boto3.client")
def test_download_ml_models_from_s3_logs_info_messages(mock_boto_client: MagicMock, mock_logging: MagicMock) -> None:
    """Test that info messages are logged during download process."""
    mock_s3_client = MagicMock()
    mock_boto_client.return_value = mock_s3_client

    model_file = "/tmp/test_model.onnx"
    vectorizer_file = "/tmp/test_vectorizer.pkl"

    # Call the function
    app_utilities.download_ml_models_from_s3(model_file, vectorizer_file)

    # Verify info messages were logged
    assert mock_logging.info.call_count == 2
    info_calls = [call[0][0] for call in mock_logging.info.call_args_list]
    assert any("Downloading model file from S3" in call for call in info_calls)
    assert any("Downloading vectorizer file from S3" in call for call in info_calls)


@patch("src.python_src.util.app_utilities.boto3.client")
def test_download_ml_models_from_s3_with_custom_paths(mock_boto_client: MagicMock) -> None:
    """Test download with custom file paths."""
    mock_s3_client = MagicMock()
    mock_boto_client.return_value = mock_s3_client

    custom_model_file = "/custom/path/my_model.onnx"
    custom_vectorizer_file = "/custom/path/my_vectorizer.pkl"

    # Call the function with custom paths
    result = app_utilities.download_ml_models_from_s3(custom_model_file, custom_vectorizer_file)

    # Verify return values match input
    assert result == (custom_model_file, custom_vectorizer_file)

    # Verify downloads were called with custom paths
    app_config = app_utilities.app_config
    expected_bucket = app_config["ml_classifier"]["aws"]["bucket"]["staging"]  # default env
    expected_model_key = app_config["ml_classifier"]["aws"]["model"]
    expected_vectorizer_key = app_config["ml_classifier"]["aws"]["vectorizer"]

    mock_s3_client.download_file.assert_any_call(expected_bucket, expected_model_key, custom_model_file)
    mock_s3_client.download_file.assert_any_call(expected_bucket, expected_vectorizer_key, custom_vectorizer_file)


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
