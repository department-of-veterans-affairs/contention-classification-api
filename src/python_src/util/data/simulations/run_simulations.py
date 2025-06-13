"""
This script runs a set of input conditions through the classifiers
and outputs their results to file.

The intent is to gather outputs for comparing and tracking behavior of the classifiers.


### Inputs ###
The input file is expected to be a csv with these columns: text_to_classify, expected_classification
As an example of rows in an input file:

acne,9016
adjustment disorder,8989
agoraphobia,8989
alopecia,9016

### Outputs ###

For each classifier being considered, two files are created:
1. a file that shows computed scores for the classifier (eg accuracy, precision, recall)
2. a file that shows the predictions made by the classifier for the inputs.
As an example of rows in this output file:

text_to_classify,expected_classification,prediction,is_accurate
acne,9016,9016,True
adjustment disorder,8989,,False
agoraphobia,8989,8989,True
alopecia,9016,1234,False

Additionally,if more than one classifier is being considered, then an output file of the predictions across all of the classifiers is created.
As an example of rows in this output file:

text_to_classify,expected_classification,prediction_by_model_a,is_model_a_accurate,prediction_by_model_b,is_model_b_accurate
acne,9016,9016,True,9012,False
adjustment disorder,8989,9012,False,8989,True
agoraphobia,8989,8989,True,8989,True
alopecia,9016,1234,False,9012,False

Usage: (from the codebase root directory)
    poetry run python src/python_src/util/data/simulations/run_simulations.py

"""

import os
import time
from datetime import datetime
from typing import Callable, List, Tuple


from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report

from python_src.util.app_utilities import expanded_lookup_table

SIMULATIONS_DIR = "src/python_src/util/data/simulations/"
INPUT_FILE = "inputs_mini.csv"
TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


## start of classifiers ###
def get_classification_from_production_classifier(conditions: List[str]) -> List[str]:

    predicted_classifications = []

    for condition in conditions:
        try:
            prediction = str(expanded_lookup_table.get(condition).get("classification_code"))
        except Exception as e:
            prediction = "no-classification"
        predicted_classifications.append(prediction)
    return predicted_classifications

def get_classification_from_respiratory_classifier(conditions: List[str]) -> List[str]:
    """For demo purposes: a classifier that always predicts the label '9012' (classification: respiratory)"""
    return ['9016'] * len(conditions)

## end of classifiers ###


def run_inputs_against_classifier(
    conditions_to_test: List[str],
    classifier_function: Callable[
        [
            str,
        ],
        str,
    ]
) -> List[str]:
    """Returns the list of predictions"""
    print(f"\n--- {classifier_function.__name__} -------")

    start_time = time.time()
    
    classifier_predictions = classifier_function(conditions_to_test)

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {round(execution_time, 4)} seconds")

    return classifier_predictions




def _write_scores_to_file(classification_report: str
, file_prefix: str) -> str:
    filename = f"{file_prefix}_{TIMESTAMP}_scores.csv"

    with open(os.path.join(SIMULATIONS_DIR, "outputs", filename), "w") as f:
        f.writelines(classification_report)
    return filename


def _write_predictions_to_file(conditions_to_test: List[str], expected_classifications: List[str], predictions: List[str], file_prefix: str) -> str:
    filename = f"{file_prefix}_{TIMESTAMP}.csv"

    assert len(conditions_to_test) == len(expected_classifications) == len(predictions)

    os.makedirs(os.path.join(SIMULATIONS_DIR, "outputs"), exist_ok=True)
    with open(os.path.join(SIMULATIONS_DIR, "outputs", filename), "w") as f:
        f.write("text_to_classify,expected_classification,prediction,is_accurate\n")

        for i in range(len(conditions_to_test)):
            f.write(f"{conditions_to_test[i]},{expected_classifications[i]},{predictions[i]},{str(expected_classifications[i])==str(predictions[i])}\n")

    return filename

def _write_aggregate_predictions_to_file(conditions_to_test: List[str], expected_classifications: List[str], predictions_across_classifiers, file_prefix: str) -> str:

    filename = f"{file_prefix}_{TIMESTAMP}.csv"

    assert len(conditions_to_test) == len(expected_classifications)

    column_names = ['text_to_classify', 'expected_classification']
    for i in predictions_across_classifiers:
        assert len(i[1]) == len(expected_classifications)
        column_names += [i[0], f"{i[0]} accurate?"]

    os.makedirs(os.path.join(SIMULATIONS_DIR, "outputs"), exist_ok=True)
    with open(os.path.join(SIMULATIONS_DIR, "outputs", filename), "w") as f:
        f.write(f"{','.join(column_names)}\n")

        for i in range(len(conditions_to_test)):
            
            row_to_write = f"{conditions_to_test[i]},{expected_classifications[i]}"

            for classifier_predictions in predictions_across_classifiers:
                row_to_write += f",{classifier_predictions[1][i]},{classifier_predictions[1][i] == expected_classifications[i]}"

            f.write(f"{row_to_write}\n")
    return filename

def _get_input_from_file() -> Tuple[List[str], List[str]]:

    conditions_to_test = []
    expected_classifications = []

    with open(os.path.join(SIMULATIONS_DIR, INPUT_FILE), "r") as f:
        file_data = f.readlines()

        for row in file_data:
            row = row.split("#")[0]
            if len(row.split(",")) != 2:
                continue
            
            tokens = [token.strip() for token in row.split(",")]
            conditions_to_test.append(tokens[0])
            expected_classifications.append(tokens[1])

    return (conditions_to_test, expected_classifications)


if __name__ == "__main__":
    conditions_to_test, expected_classifications = _get_input_from_file()

    labels = list(set(expected_classifications))
    labels.sort()

    classifiers: List[
        Tuple[
            Callable[
                [
                    List[str],
                ],
                List[str],
            ],
            str,
        ]
    ] = [
        (get_classification_from_production_classifier, "production_classifier"),
        (get_classification_from_respiratory_classifier, "respiratory_classifier"),
    ]

    predictions_across_classifiers = []

    for classifier_function, descriptive_name in classifiers:
        
        predictions = run_inputs_against_classifier(conditions_to_test, classifier_function)
        
        predictions_across_classifiers.append((descriptive_name, predictions))

        predictions_file = _write_predictions_to_file(conditions_to_test, expected_classifications, predictions, descriptive_name)

        computed_scores = classification_report(expected_classifications, predictions, target_names=labels, zero_division=1)

        scores_file = _write_scores_to_file(computed_scores, descriptive_name)

        print(f"Outputs: {predictions_file}, {scores_file}\n")

    if len(classifiers) > 1:
        _write_aggregate_predictions_to_file(conditions_to_test, expected_classifications, predictions_across_classifiers, "aggregate_predictions")