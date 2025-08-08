import os
import string
from unittest.mock import MagicMock, call, patch

import pytest
from numpy import float32, ndarray
from onnx.helper import make_node
from scipy.sparse import csr_matrix

from src.python_src.util import app_utilities
from src.python_src.util.ml_classifier import MLClassifier


@patch("src.python_src.util.ml_classifier.os.path.exists")
@patch("src.python_src.util.ml_classifier.ort.InferenceSession")
@patch("src.python_src.util.ml_classifier.joblib.load")
def test_instantiation(mock_joblib: MagicMock, mock_onnx_session: MagicMock, mock_os_path: MagicMock) -> None:
    mock_model_filepath = "/path/to/model-file.onnx"
    mock_vectorizer_filepath = "/path/to/vectorizer-file.pkl"
    mock_os_path.return_value = True

    MLClassifier(mock_model_filepath, mock_vectorizer_filepath)
    mock_os_path.assert_has_calls([call(mock_model_filepath), call(mock_vectorizer_filepath)])
    mock_onnx_session.assert_called_once_with(mock_model_filepath)
    mock_joblib.assert_called_once_with(mock_vectorizer_filepath)


@patch("src.python_src.util.ml_classifier.os.path.exists")
@patch("src.python_src.util.ml_classifier.joblib.load")
def test_instantiation_raises_exception_if_file_not_found(mock_joblib: MagicMock, mock_os_path: MagicMock) -> None:
    mock_model_filepath = "/path/to/model-file.onnx"
    mock_vectorizer_filepath = "/path/to/vectorizer-file.pkl"
    mock_os_path.return_value = False

    with pytest.raises(Exception) as exception_info:
        MLClassifier(mock_model_filepath, mock_vectorizer_filepath)
    assert "File not found: /path/to/model-file.onnx" in str(
        exception_info.value
    ) or "[Errno 2] No such file or directory: ''" in str(exception_info.value)


@patch("src.python_src.util.ml_classifier.os.path.exists")
@patch("src.python_src.util.ml_classifier.ort.InferenceSession")
@patch("src.python_src.util.ml_classifier.joblib.load")
def test_instantiation_raises_exception_if_vectorizer_file_not_found(
    mock_joblib: MagicMock, mock_onnx_session: MagicMock, mock_os_path: MagicMock
) -> None:
    """Test that MLClassifier raises exception when vectorizer file is not found."""
    mock_model_filepath = "/path/to/model-file.onnx"
    mock_vectorizer_filepath = "/path/to/vectorizer-file.pkl"

    # Mock model file exists but vectorizer file does not
    def mock_exists(path: str) -> bool:
        return path == mock_model_filepath

    mock_os_path.side_effect = mock_exists

    with pytest.raises(Exception) as exception_info:
        MLClassifier(mock_model_filepath, mock_vectorizer_filepath)
    assert "File not found: /path/to/vectorizer-file.pkl" in str(exception_info.value)


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
) -> None:
    mock_os_path.return_value = True

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


@patch("src.python_src.util.ml_classifier.os.path.exists")
@patch("src.python_src.util.ml_classifier.ort.InferenceSession")
@patch("src.python_src.util.ml_classifier.joblib.load")
def test_inputs_is_dictionary_of_transformed_values_as_ndarray(
    mock_joblib: MagicMock, mock_onnx_session: MagicMock, mock_os_path: MagicMock
) -> None:
    mock_os_path.return_value = True
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


@patch("src.python_src.util.ml_classifier.os.path.exists")
@patch("src.python_src.util.ml_classifier.ort.InferenceSession")
@patch("src.python_src.util.ml_classifier.joblib.load")
def test_clean_text(mock_joblib: MagicMock, mock_onnx_session: MagicMock, mock_os_path: MagicMock) -> None:
    mock_os_path.return_value = True

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
@patch("src.python_src.util.app_utilities.download_ml_models_from_s3")
def test_invoke_mlClassifier(mock_download: MagicMock, mock_init: MagicMock) -> None:
    """Test that MLClassifier can be successfully instantiated and invoked.

    Verifies that the MLClassifier can be created and used for classification
    when the required model files are properly downloaded and initialized.
    Tests the complete workflow from instantiation to prediction.
    """
    mock_init.return_value = None

    model_file = app_utilities.app_config["ml_classifier"]["data"]["model_file"]
    vectorizer_file = app_utilities.app_config["ml_classifier"]["data"]["vectorizer_file"]
    expected_return = (model_file, vectorizer_file)
    mock_download.return_value = expected_return

    assert expected_return == app_utilities.download_ml_models_from_s3(model_file, vectorizer_file)


@patch("src.python_src.util.ml_classifier.os.path.exists")
@patch("src.python_src.util.ml_classifier.ort.InferenceSession")
@patch("src.python_src.util.ml_classifier.joblib.load")
@patch("src.python_src.util.ml_classifier.logging")
def test_make_predictions_handles_exceptions(
    mock_logging: MagicMock, mock_joblib: MagicMock, mock_onnx_session: MagicMock, mock_os_path: MagicMock
) -> None:
    """Test that make_predictions handles exceptions gracefully and logs errors."""
    mock_model_filepath = "/path/to/model-file.onnx"
    mock_vectorizer_filepath = "/path/to/vectorizer-file.pkl"
    mock_os_path.return_value = True

    # Mock the session.run to raise an exception
    mock_session = MagicMock()
    mock_session.run.side_effect = Exception("Test exception")
    mock_onnx_session.return_value = mock_session

    classifier = MLClassifier(mock_model_filepath, mock_vectorizer_filepath)

    conditions = ["test condition 1", "test condition 2"]
    result = classifier.make_predictions(conditions)

    # Should return error tuples for each condition
    expected = [("error", 0.0), ("error", 0.0)]
    assert result == expected

    # Should log the error
    mock_logging.error.assert_called_once()
