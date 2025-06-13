"""
This script runs a set of input conditions through the classifiers
and outputs their results to file.

The intent is to gather outputs for comparing and tracking behavior of the classifiers.


The input file is expected to be a csv with these columns: text_to_classify, expected_classification
As an example of rows in an input file:

acne,9016
adjustment disorder,8989
agoraphobia,8989
alopecia,9016


The output files will have these columns: text_to_classify, expected_classification, prediction, is_accurate.
As an example of rows in an output file:

acne,9016,9016,True
adjustment disorder,8989,,False
agoraphobia,8989,8989,True
alopecia,9016,1234,False


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


def get_respiratory_classification(conditions: List[str]) -> List[str]:
    return ['9012'] * len(conditions)


def get_skin_classification(conditions: List[str]) -> List[str]:
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
        (get_respiratory_classification, "respiratory_classification_always"),
        (get_skin_classification, "skin_classifiction_always"),
        #(get_classification_from_ml_classifier, "ml_classifier"),
        # (get_classification_from_stacked_classifier, "stacked"),
        # (get_classification_from_reverse_stacked_classifier, "reverse_stacked"),
    ]

    for classifier_function, descriptive_name in classifiers:
        
        predictions = run_inputs_against_classifier(conditions_to_test, classifier_function)

        predictions_file = _write_predictions_to_file(conditions_to_test, expected_classifications, predictions, descriptive_name)

        computed_scores = classification_report(expected_classifications, predictions, target_names=labels, zero_division=1)

        scores_file = _write_scores_to_file(computed_scores, descriptive_name)

        print(f"Outputs: {predictions_file}, {scores_file}")
