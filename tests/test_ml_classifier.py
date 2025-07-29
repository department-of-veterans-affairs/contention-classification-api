import os
import string
from unittest.mock import MagicMock, call, patch

import pytest
from numpy import float32, ndarray
from onnx.helper import make_node
from scipy.sparse import csr_matrix

from src.python_src.util import app_utilities
from src.python_src.util.app_utilities import app_config, model_file, vectorizer_file
from src.python_src.util.ml_classifier import MLClassifier


# Mock JSON data for BRD classifications
@pytest.fixture
def mock_brd_json_data() -> str:
    return """{
    "1230": "Musculoskeletal - Osteomyelitis",
    "8989": "Mental Disorders",
    "8997": "Musculoskeletal - Knee",
    "9012": "Respiratory",
    "9016": "Skin"
}"""


# Mock CSV data for contention classifications
@pytest.fixture
def mock_contention_csv_data() -> str:
    return """contention_text,classification_code,classification_name,active
PTSD,8989,Mental Disorders,Active
Knee pain,8997,Musculoskeletal - Knee,Active
Asthma,9012,Respiratory,Active
Acne,9016,Skin,Active
Tinnitus,8968,Auditory,Active"""


# Mock simulation CSV data
@pytest.fixture
def mock_simulation_csv_data() -> str:
    return """text_to_classify,expected_classification
PTSD (post-traumatic stress disorder),8989
acl tear right,8997
asthma chronic,9012
acne severe,9016
tinnitus ringing ears,8968"""


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
    mock_outputs_for_session.return_value = ["output_label"]
    mock_inputs_for_session.return_value = {"input_label": ndarray(1)}
    classifier.session.run = MagicMock()
    classifier.session.run.return_value = [["lorem", "ipsum", "dolor"]]
    mock_clean_text.return_value = "asthma"

    predictions = classifier.make_predictions(["ASTHMA", "asthma", "asth.ma"])
    mock_clean_text.assert_has_calls([call("ASTHMA"), call("asthma"), call("asth.ma")])
    mock_outputs_for_session.assert_called_once()
    mock_inputs_for_session.assert_called_with(["asthma", "asthma", "asthma"])
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


@patch("src.python_src.util.ml_classifier.os.path.exists")
@patch("src.python_src.util.ml_classifier.ort.InferenceSession")
@patch("src.python_src.util.ml_classifier.joblib.load")
def test_clean_text(
    mock_joblib: MagicMock,
    mock_onnx_session: MagicMock,
    mock_os_path: MagicMock,
) -> None:
    mock_os_path.return_value = True

    classifier = MLClassifier("model.onnx", "vectorizer.pkl")
    assert classifier.clean_text("LOREM") == "lorem"
    assert classifier.clean_text("a.b!c?d") == "abcd"
    assert classifier.clean_text(f"abc${string.punctuation} def") == "abc def"
    assert classifier.clean_text("lorem    ipsum  dolor") == "lorem ipsum dolor"
    assert classifier.clean_text(" Lorem Ipsum Dolor ") == "lorem ipsum dolor"


def test_app_config_values_exist() -> None:
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

    model_file_path = app_config["ml_classifier"]["model_file"]
    assert model_file_path
    assert model_file_path.lower().endswith(".onnx")

    vectorizer_file_path = app_config["ml_classifier"]["vectorizer_file"]
    assert vectorizer_file_path
    assert vectorizer_file_path.lower().endswith(".pkl")


@patch("src.python_src.util.ml_classifier.boto3.client")
def test_s3(mock_boto_client: MagicMock) -> None:
    mock_boto_client.return_value.download_file = MagicMock()
    s3_client = mock_boto_client.return_value

    # Call the download_file methods
    s3_client.download_file(
        app_config["ml_classifier"]["aws"]["bucket"],
        app_config["ml_classifier"]["aws"]["model"],
        model_file,
    )
    s3_client.download_file(
        app_config["ml_classifier"]["aws"]["bucket"],
        app_config["ml_classifier"]["aws"]["vectorizer"],
        vectorizer_file,
    )

    # Assert download_file was called exactly twice
    assert s3_client.download_file.call_count == 2

    # Assert download_file was called with the correct arguments
    s3_client.download_file.assert_has_calls(
        [
            call(
                app_config["ml_classifier"]["aws"]["bucket"],
                app_config["ml_classifier"]["aws"]["model"],
                model_file,
            ),
            call(
                app_config["ml_classifier"]["aws"]["bucket"],
                app_config["ml_classifier"]["aws"]["vectorizer"],
                vectorizer_file,
            ),
        ]
    )


@patch("src.python_src.util.ml_classifier.MLClassifier.__init__")
@patch("src.python_src.util.ml_classifier.MLClassifier.download_models_from_s3")
def test_invoke_mlClassifier(mock_download: MagicMock, mock_init: MagicMock) -> None:
    mock_init.return_value = None

    model_directory_path = app_utilities.app_config["ml_classifier"]["data"]["directory"]
    model_file = app_utilities.app_config["ml_classifier"]["model_file"]
    vectorizer_file = app_utilities.app_config["ml_classifier"]["vectorizer_file"]
    expected_return = (model_directory_path, model_file, vectorizer_file)
    mock_download.return_value = expected_return

    classifier = MLClassifier()
    assert expected_return == classifier.download_models_from_s3(
        model_directory_path=model_directory_path, model_file=model_file, vectorizer_file=vectorizer_file
    )
