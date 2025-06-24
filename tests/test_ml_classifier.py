from unittest.mock import MagicMock, call, patch

import pytest
from numpy import float32, ndarray
from onnx.helper import make_node
from scipy.sparse import csr_matrix

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
    assert "File not found: /path/to/model-file.onnx" in str(exception_info.value)


@patch("src.python_src.util.ml_classifier.os.path.exists")
@patch("src.python_src.util.ml_classifier.ort.InferenceSession")
@patch("src.python_src.util.ml_classifier.joblib.load")
def test_classify_conditions(mock_joblib: MagicMock, mock_onnx_session: MagicMock, mock_os_path: MagicMock) -> None:
    mock_os_path.return_value = True

    classifier = MLClassifier("model.onnx", "vectorizer.pkl")
    classifier.get_outputs_for_session = MagicMock()
    classifier.get_outputs_for_session.return_value = ["output_label"]
    classifier.get_inputs_for_session = MagicMock()
    classifier.get_inputs_for_session.return_value = {"input_label": ndarray(1)}
    classifier.session.run = MagicMock()
    classifier.session.run.return_value = [["lorem", "ipsum", "dolor"]]

    predictions = classifier.make_predictions(["asthma", "emphysema", "hearing loss"])
    classifier.get_outputs_for_session.assert_called_once()
    classifier.get_inputs_for_session.assert_called_with(["asthma", "emphysema", "hearing loss"])
    classifier.session.run.assert_called_with(["output_label"], {"input_label": ndarray(1)})
    assert predictions == ["lorem", "ipsum", "dolor"]


@patch("src.python_src.util.ml_classifier.os.path.exists")
@patch("src.python_src.util.ml_classifier.ort.InferenceSession")
@patch("src.python_src.util.ml_classifier.joblib.load")
def test_inputs_is_dictionary_of_transformed_values_as_ndarray(
    mock_joblib: MagicMock, mock_onnx_session: MagicMock, mock_os_path: MagicMock
) -> None:
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
