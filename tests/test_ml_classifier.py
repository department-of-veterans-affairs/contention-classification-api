from unittest.mock import MagicMock, patch

import pytest

from src.python_src.util.ml_classifier import MLClassifier

@patch("src.python_src.util.ml_classifier.os.path.exists")
@patch("src.python_src.util.ml_classifier.joblib.load")
def test_instantiation(mock_joblib: MagicMock, mock_os_path: MagicMock) -> None:
    mock_filepath = "/path/to/model-file.pkl"
    mock_os_path.return_value = True
    
    MLClassifier(mock_filepath)
    mock_os_path.assert_called_once_with(mock_filepath)
    mock_joblib.assert_called_once_with(mock_filepath)


@patch("src.python_src.util.ml_classifier.os.path.exists")
@patch("src.python_src.util.ml_classifier.joblib.load")
def test_instantiation_raises_exception_if_file_not_found(mock_joblib: MagicMock, mock_os_path: MagicMock) -> None:
    mock_filepath = "/path/to/model-file.pkl"
    mock_os_path.return_value = False

    with pytest.raises(Exception) as exception_info:
        MLClassifier(mock_filepath)
    assert "File not found: /path/to/model-file.pkl" in str(exception_info.value)

 
@patch("src.python_src.util.ml_classifier.os.path.exists")
@patch("src.python_src.util.ml_classifier.joblib.load")
def test_classify_conditions(mock_joblib: MagicMock, mock_os_path: MagicMock) -> None:
    mock_os_path.return_value = True
    classifier = MLClassifier("lorem.pkl")
    classifier.model.predict.return_value = ['lorem', 'ipsum', 'dolor']

    predictions = classifier.make_predictions(['asthma', 'emphysema', 'hearing loss'])
    classifier.model.predict.assert_called_with(['asthma', 'emphysema', 'hearing loss'])
    assert predictions == ['lorem', 'ipsum', 'dolor']


@patch("src.python_src.util.ml_classifier.os.path.exists")
@patch("src.python_src.util.ml_classifier.joblib.load")
def test_classify_conditions_handles_empty_predictions(mock_joblib: MagicMock, mock_os_path: MagicMock) -> None:
    mock_os_path.return_value = True
    classifier = MLClassifier("lorem.pkl")
    classifier.model.predict.return_value = ['', '', 'lorem']

    predictions = classifier.make_predictions(['asthma', 'emphysema', 'hearing loss'])
    classifier.model.predict.assert_called_with(['asthma', 'emphysema', 'hearing loss'])
    assert predictions == ['no-classification', 'no-classification', 'lorem']
