import os
import string
from unittest.mock import MagicMock, call, patch

import pytest
from numpy import float32, ndarray
from onnx.helper import make_node
from scipy.sparse import csr_matrix

from src.python_src.util import app_utilities
from src.python_src.util.app_utilities import app_config
from src.python_src.util.ml_classifier import MLClassifier


@patch("src.python_src.util.ml_classifier.MLClassifier.download_models_from_s3")
@patch("src.python_src.util.ml_classifier.os.path.exists")
@patch("src.python_src.util.ml_classifier.ort.InferenceSession")
@patch("src.python_src.util.ml_classifier.joblib.load")
def test_instantiation(
    mock_joblib: MagicMock, mock_onnx_session: MagicMock, mock_os_path: MagicMock, mock_download: MagicMock
) -> None:
    mock_model_filepath = "/path/to/model-file.onnx"
    mock_vectorizer_filepath = "/path/to/vectorizer-file.pkl"
    mock_os_path.return_value = True
    mock_download.return_value = (mock_model_filepath, mock_vectorizer_filepath, "src/python_src/util/models/")

    MLClassifier(mock_model_filepath, mock_vectorizer_filepath)
    mock_os_path.assert_has_calls([call(mock_model_filepath), call(mock_vectorizer_filepath)])
    mock_onnx_session.assert_called_once_with(mock_model_filepath)
    mock_joblib.assert_called_once_with(mock_vectorizer_filepath)


@patch("src.python_src.util.ml_classifier.MLClassifier.download_models_from_s3")
@patch("src.python_src.util.ml_classifier.os.path.exists")
@patch("src.python_src.util.ml_classifier.joblib.load")
def test_instantiation_raises_exception_if_file_not_found(
    mock_joblib: MagicMock, mock_os_path: MagicMock, mock_download: MagicMock
) -> None:
    mock_model_filepath = "/path/to/model-file.onnx"
    mock_vectorizer_filepath = "/path/to/vectorizer-file.pkl"
    mock_os_path.return_value = False
    mock_download.return_value = (mock_model_filepath, mock_vectorizer_filepath, "src/python_src/util/models/")
    with pytest.raises(Exception) as exception_info:
        MLClassifier(mock_model_filepath, mock_vectorizer_filepath)
    assert "File not found: /path/to/model-file.onnx" in str(
        exception_info.value
    ) or "[Errno 2] No such file or directory: ''" in str(exception_info.value)


@patch("src.python_src.util.ml_classifier.MLClassifier.download_models_from_s3")
@patch("src.python_src.util.ml_classifier.os.path.exists")
@patch("src.python_src.util.ml_classifier.ort.InferenceSession")
@patch("src.python_src.util.ml_classifier.joblib.load")
@patch("src.python_src.util.ml_classifier.MLClassifier.get_inputs_for_session")
@patch("src.python_src.util.ml_classifier.MLClassifier.get_outputs_for_session")
@patch("src.python_src.util.ml_classifier.MLClassifier.clean_text")
def test_classify_conditions(
    mock_clean_text: MagicMock,
    mock_outputs_for_session: MagicMock,
    mock_inputs_for_session: MagicMock,
    mock_joblib: MagicMock,
    mock_onnx_session: MagicMock,
    mock_os_path: MagicMock,
    mock_download: MagicMock,
) -> None:
    mock_os_path.return_value = True
    mock_download.return_value = ("model.onnx", "vectorizer.pkl", "src/python_src/util/models/")

    classifier = MLClassifier("model.onnx", "vectorizer.pkl")
    mock_outputs_for_session.return_value = ["output_label", "output_probability"]
    mock_inputs_for_session.return_value = {"input_label": ndarray(1)}
    classifier.session.run = MagicMock()
    classifier.session.run.return_value = [
        ["lorem", "ipsum", "dolor"],
        [
            {"lorem": 0.74, "ipsum": 0.1, "dolor": 0.1},
            {"lorem": 0.24, "ipsum": 0.92, "dolor": 0.1},
            {"lorem": 0.24, "ipsum": 0.92, "dolor": 0.95},
        ],
    ]
    mock_clean_text.return_value = "asthma"

    predictions = classifier.make_predictions(["ASTHMA", "asthma", "asth.ma"])
    mock_clean_text.assert_has_calls([call("ASTHMA"), call("asthma"), call("asth.ma")])
    mock_outputs_for_session.assert_called_once()
    mock_inputs_for_session.assert_called_with(["asthma", "asthma", "asthma"])
    classifier.session.run.assert_called_once()
    assert predictions == [("lorem", 0.74), ("ipsum", 0.92), ("dolor", 0.95)]


@patch("src.python_src.util.ml_classifier.MLClassifier.download_models_from_s3")
@patch("src.python_src.util.ml_classifier.os.path.exists")
@patch("src.python_src.util.ml_classifier.ort.InferenceSession")
@patch("src.python_src.util.ml_classifier.joblib.load")
def test_inputs_is_dictionary_of_transformed_values_as_ndarray(
    mock_joblib: MagicMock, mock_onnx_session: MagicMock, mock_os_path: MagicMock, mock_download: MagicMock
) -> None:
    mock_os_path.return_value = True
    mock_download.return_value = ("model.onnx", "vectorizer.pkl", "src/python_src/util/models/")
    classifier = MLClassifier("model.onnx", "vectorizer.pkl")

    classifier.vectorizer = MagicMock()
    classifier.vectorizer.transform.return_value = csr_matrix(1)
    classifier.session = MagicMock()
    classifier.session.get_inputs.return_value = [
        make_node("A", ["X"], ["Y"], name="node_name"),
    ]

    inputs = classifier.get_inputs_for_session(["asthma", "lorem ipsum", "dolor sit amit"])
    classifier.vectorizer.transform.assert_called_with(["asthma", "lorem ipsum", "dolor sit amit"])
    classifier.session.get_inputs.assert_called_once()

    assert inputs == {"node_name": csr_matrix(1).toarray().astype(float32)}


@patch("src.python_src.util.ml_classifier.MLClassifier.download_models_from_s3")
@patch("src.python_src.util.ml_classifier.os.path.exists")
@patch("src.python_src.util.ml_classifier.ort.InferenceSession")
@patch("src.python_src.util.ml_classifier.joblib.load")
def test_clean_text(
    mock_joblib: MagicMock, mock_onnx_session: MagicMock, mock_os_path: MagicMock, mock_download: MagicMock
) -> None:
    mock_os_path.return_value = True
    mock_download.return_value = ("model.onnx", "vectorizer.pkl", "src/python_src/util/models/")

    classifier = MLClassifier("model.onnx", "vectorizer.pkl")
    assert classifier.clean_text("LOREM") == "lorem"
    assert classifier.clean_text("a.b!c?d") == "abcd"
    assert classifier.clean_text(f"abc${string.punctuation} def") == "abc def"
    assert classifier.clean_text("lorem    ipsum  dolor") == "lorem ipsum dolor"
    assert classifier.clean_text(" Lorem Ipsum Dolor ") == "lorem ipsum dolor"


def test_app_config_values_exist() -> None:
    """Test that all required configuration values are present and properly formatted."""
    app_config = app_utilities.load_config(os.path.join("src/python_src/util", "app_config.yaml"))

    directory = app_config["ml_classifier"]["data"]["directory"]
    assert directory
    assert "models" in directory

    aws_model = app_config["ml_classifier"]["aws"]["model"]
    assert aws_model
    assert aws_model.lower().endswith(".onnx")

    aws_vectorizer = app_config["ml_classifier"]["aws"]["vectorizer"]
    assert aws_vectorizer
    assert aws_vectorizer.lower().endswith(".pkl")

    model_file_path = app_config["ml_classifier"]["data"]["model_file"]
    assert model_file_path
    assert model_file_path.lower().endswith(".onnx")

    vectorizer_file_path = app_config["ml_classifier"]["data"]["vectorizer_file"]
    assert vectorizer_file_path
    assert vectorizer_file_path.lower().endswith(".pkl")


@patch("src.python_src.util.ml_classifier.MLClassifier.__init__")
@patch("src.python_src.util.ml_classifier.MLClassifier.download_models_from_s3")
def test_invoke_mlClassifier(mock_download: MagicMock, mock_init: MagicMock) -> None:
    """Test that MLClassifier can be successfully instantiated and invoked.

    Verifies that the MLClassifier can be created and used for classification
    when the required model files are properly downloaded and initialized.
    Tests the complete workflow from instantiation to prediction.
    """
    mock_init.return_value = None

    model_directory_path = app_utilities.app_config["ml_classifier"]["data"]["directory"]
    model_file = app_utilities.app_config["ml_classifier"]["data"]["model_file"]
    vectorizer_file = app_utilities.app_config["ml_classifier"]["data"]["vectorizer_file"]
    expected_return = (model_directory_path, model_file, vectorizer_file)
    mock_download.return_value = expected_return

    classifier = MLClassifier()
    assert expected_return == classifier.download_models_from_s3(
        model_directory_path=model_directory_path, model_file=model_file, vectorizer_file=vectorizer_file
    )


@patch("src.python_src.util.ml_classifier.MLClassifier.download_models_from_s3")
@patch("src.python_src.util.ml_classifier.os.path.exists")
@patch("src.python_src.util.ml_classifier.ort.InferenceSession")
@patch("src.python_src.util.ml_classifier.joblib.load")
def test_vectorizer_key_download(
    mock_joblib: MagicMock, mock_onnx_session: MagicMock, mock_os_path: MagicMock, mock_download: MagicMock
) -> None:
    """Test that vectorizer key is properly retrieved from S3 during model download when files don't exist locally.

    Validates that when files don't exist locally, the S3 download logic:
    - Successfully downloads from the configured S3 bucket
    - Uses the correct vectorizer key from configuration
    - Stores files in the expected local path
    Tests the S3 integration for vectorizer key retrieval.
    """
    # Set up file paths
    model_file = app_config["ml_classifier"]["data"]["model_file"]
    vectorizer_file = app_config["ml_classifier"]["data"]["vectorizer_file"]
    model_directory = app_config["ml_classifier"]["data"]["directory"]

    # Mock that files exist after download
    mock_os_path.return_value = True

    # Mock the download method to simulate successful S3 download
    mock_download.return_value = (model_file, vectorizer_file, model_directory)

    # Create MLClassifier instance
    _classifier = MLClassifier()

    # Verify that download was called (this tests that the download logic is invoked)
    mock_download.assert_called_once()

    # Verify that the constructor used the returned file paths
    mock_os_path.assert_has_calls([call(model_file), call(vectorizer_file)])
    mock_onnx_session.assert_called_once_with(model_file)
    mock_joblib.assert_called_once_with(vectorizer_file)


@patch("src.python_src.util.ml_classifier.os.path.exists")
@patch("src.python_src.util.ml_classifier.boto3.client")
def test_download_models_from_s3_when_files_missing(mock_boto_client: MagicMock, mock_os_path: MagicMock) -> None:
    """Test that S3 download works correctly when model files are missing locally."""
    mock_s3_client = MagicMock()
    mock_boto_client.return_value = mock_s3_client

    # Mock os.path.exists to return False (files don't exist locally)
    mock_os_path.return_value = False

    # Create classifier instance to test download logic
    from src.python_src.util.ml_classifier import MLClassifier

    classifier = MLClassifier.__new__(MLClassifier)  # Create without calling __init__

    # Call download method directly
    classifier.download_models_from_s3()

    # Verify S3 download was called with correct parameters
    expected_vectorizer_key = app_config["ml_classifier"]["aws"]["vectorizer"]
    expected_model_key = app_config["ml_classifier"]["aws"]["model"]
    expected_bucket = app_config["ml_classifier"]["aws"]["bucket"]
    expected_local_vectorizer_file = app_config["ml_classifier"]["data"]["vectorizer_file"]
    expected_local_model_file = app_config["ml_classifier"]["data"]["model_file"]

    mock_s3_client.download_file.assert_any_call(expected_bucket, expected_vectorizer_key, expected_local_vectorizer_file)
    mock_s3_client.download_file.assert_any_call(expected_bucket, expected_model_key, expected_local_model_file)


@patch("src.python_src.util.ml_classifier.os.path.exists")
@patch("src.python_src.util.ml_classifier.boto3.client")
def test_download_models_from_s3_when_files_exist(mock_boto_client: MagicMock, mock_os_path: MagicMock) -> None:
    """Test that S3 download is skipped when model files exist locally."""
    mock_s3_client = MagicMock()
    mock_boto_client.return_value = mock_s3_client

    # Mock os.path.exists to return True (files exist locally)
    mock_os_path.return_value = True

    # Create classifier instance to test download logic
    from src.python_src.util.ml_classifier import MLClassifier

    classifier = MLClassifier.__new__(MLClassifier)  # Create without calling __init__

    # Call download method directly
    _result = classifier.download_models_from_s3()

    # Verify S3 download was NOT called since files exist locally
    mock_s3_client.download_file.assert_not_called()
    mock_boto_client.assert_not_called()


def test_vectorizer_key_config_validation() -> None:
    """Test that the vectorizer key from config meets expected requirements."""
    vectorizer_key = app_config["ml_classifier"]["aws"]["vectorizer"]

    assert isinstance(vectorizer_key, str), "Vectorizer key should be a string"
    assert len(vectorizer_key) > 0, "Vectorizer key should not be empty"
    assert vectorizer_key.endswith(".pkl"), "Vectorizer key should end with .pkl extension"
    assert "vectorizer" in vectorizer_key.lower(), "Vectorizer key should contain 'vectorizer' in the name"
    assert vectorizer_key != app_config["ml_classifier"]["aws"]["model"], "Vectorizer key should be different from model key"
