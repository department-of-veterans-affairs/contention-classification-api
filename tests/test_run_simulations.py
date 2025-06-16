import os
import tempfile
from unittest.mock import patch

from src.python_src.util.data.simulations.classifiers import BaseClassifierForSimulation
from src.python_src.util.data.simulations.run_simulations import (
    _get_input_from_file,
    _write_aggregate_predictions_to_file,
    _write_metrics_to_file,
    _write_predictions_to_file,
)

METRICS_REPORT_CONTENT = '''
              precision    recall  f1-score   support

      yellow       1.00      1.00      1.00         1
      orange       1.00      1.00      1.00         3
      purple       1.00      1.00      1.00         6

    accuracy                           1.00        10
   macro avg       1.00      1.00      1.00        10
weighted avg       1.00      1.00      1.00        10
'''

PREDICTIONS_CSV_CONTENT = '''text_to_classify,expected_classification,prediction,is_accurate
acne,9016,9016,True
alopecia,9016,9016,True
asthma,9012,9032,False
psoriasis,9016,9016,True
vitiligo,9016,9012,False
'''

AGGREGATE_PREDICTIONS_CSV_CONTENT = '''text_to_classify,expected_classification,apple_prediction,\
apple_is_accurate,banana_prediction,banana_is_accurate
acne,9016,9016,True,9000,False
alopecia,9016,9016,True,9001,False
asthma,9012,9032,False,9002,False
psoriasis,9016,9016,True,9003,False
vitiligo,9016,9012,False,9016,True
'''

SAMPLE_INPUT_FILE_CONTENT = '''
# a comment
acne,9016
alopecia,9016
eczema,9016
gallstones,8968
psoriasis,9016
'''


@patch('src.python_src.util.data.simulations.run_simulations.SIMULATIONS_DIR', tempfile.tempdir)
@patch('src.python_src.util.data.simulations.run_simulations.INPUT_FILE', "inputs_mini.csv")
def test_get_conditions_to_test_from_input_file() -> None:
    os.makedirs(str(tempfile.tempdir), exist_ok=True)
    with open(os.path.join(str(tempfile.tempdir), "inputs_mini.csv"), 'w') as f:
        f.write(SAMPLE_INPUT_FILE_CONTENT)

    conditions_to_test, expected_classifications = _get_input_from_file()
    assert conditions_to_test == ['acne', 'alopecia', 'eczema', 'gallstones', 'psoriasis']
    assert expected_classifications == ['9016', '9016', '9016', '8968', '9016']


@patch('src.python_src.util.data.simulations.run_simulations.SIMULATIONS_DIR', tempfile.tempdir)
@patch('src.python_src.util.data.simulations.run_simulations.TIMESTAMP', "2025-06-16_12-23-34")
def test_write_metrics_to_file() -> None:
    os.makedirs(os.path.join(str(tempfile.tempdir), "outputs"), exist_ok=True)
    
    output_file = _write_metrics_to_file(METRICS_REPORT_CONTENT, "lorem")
    assert output_file == 'lorem_2025-06-16_12-23-34_metrics.txt' 

    with open(os.path.join(str(tempfile.tempdir), 'outputs', output_file), 'r') as f:
        file_content = f.read()

        assert METRICS_REPORT_CONTENT == file_content



@patch('src.python_src.util.data.simulations.run_simulations.SIMULATIONS_DIR', tempfile.tempdir)
@patch('src.python_src.util.data.simulations.run_simulations.TIMESTAMP', "2025-06-16_12-23-34")
def test_write_predictions_to_file() -> None:
    os.makedirs(os.path.join(str(tempfile.tempdir), "outputs"), exist_ok=True)
    
    conditions_to_test = ['acne', 'alopecia', 'asthma', 'psoriasis', 'vitiligo']
    expected_classifications = ['9016','9016','9012','9016','9016']
    classifier = BaseClassifierForSimulation()
    classifier.name = "demo_classifier"
    classifier.predictions = ['9016','9016','9032','9016','9012']

    output_file = _write_predictions_to_file(conditions_to_test, expected_classifications, classifier)
    assert output_file == 'demo_classifier_2025-06-16_12-23-34.csv' 

    with open(os.path.join(str(tempfile.tempdir), 'outputs', output_file), 'r') as f:
        file_content = f.read()
        assert PREDICTIONS_CSV_CONTENT == file_content


@patch('src.python_src.util.data.simulations.run_simulations.SIMULATIONS_DIR', tempfile.tempdir)
@patch('src.python_src.util.data.simulations.run_simulations.TIMESTAMP', "2025-06-16_12-23-34")
def test_write_aggregate_predictions_to_file() -> None:
    os.makedirs(os.path.join(str(tempfile.tempdir), "outputs"), exist_ok=True)
    
    conditions_to_test = ['acne', 'alopecia', 'asthma', 'psoriasis', 'vitiligo']
    expected_classifications = ['9016','9016','9012','9016','9016']
    
    classifier_apple = BaseClassifierForSimulation()
    classifier_apple.name = "apple"
    classifier_apple.predictions = ['9016','9016','9032','9016','9012']

    classifier_banana = BaseClassifierForSimulation()
    classifier_banana.name = "banana"
    classifier_banana.predictions = ['9000','9001','9002','9003','9016']

    output_file = _write_aggregate_predictions_to_file(conditions_to_test, 
        expected_classifications, [classifier_apple, classifier_banana], 'aggregate')

    assert output_file == 'aggregate_2025-06-16_12-23-34.csv' 

    with open(os.path.join(str(tempfile.tempdir), 'outputs', output_file), 'r') as f:
        file_content = f.read()
        assert AGGREGATE_PREDICTIONS_CSV_CONTENT == file_content