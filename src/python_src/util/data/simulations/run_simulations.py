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

from sklearn.metrics import accuracy_score, precision_recall_fscore_support

from python_src.util.app_utilities import expanded_lookup_table

SIMULATIONS_DIR = "src/python_src/util/data/simulations/"
INPUT_FILE = "inputs_mini.csv"
TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


## start of classifiers ###
def get_classification_from_production_classifier(condition_text: str) -> str:
    try:
        return str(expanded_lookup_table.get(condition_text).get("classification_code"))
    except Exception as e:
        print(e)

    return "no-classification"


## TODO : implement when we have the ML classifier running locally
def get_classification_from_ml_classifier(condition_text: str) -> str:
    return "no-classification"


def get_respiratory_classification(condition_text: str) -> str:
    return "9012"


def get_skin_classification(condition_text: str) -> str:
    return "9016"


def get_classification_from_stacked_classifier(condition_text: str) -> str:
    classification = get_classification_from_production_classifier(condition_text)
    if not classification:
        classification = get_classification_from_ml_classifier(condition_text)
    return classification


def get_classification_from_reverse_stacked_classifier(condition_text: str) -> str:
    classification = get_classification_from_ml_classifier(condition_text)
    if not classification:
        classification = get_classification_from_production_classifier(condition_text)
    return classification


## end of classifiers ###


def run_inputs_against_classifier(
    input_data: List[List[str]],
    classifier_function: Callable[
        [
            str,
        ],
        str,
    ],
    classifier_descriptive_name: str,
) -> None:
    print(f"\n--- {classifier_descriptive_name} -------")
    start_time = time.time()
    text_for_csv = []
    expected_values = []
    classifier_predictions = []

    for text_to_classify, expected_classification in input_data:
        classifier_prediction = ""

        try:
            classifier_prediction = classifier_function(text_to_classify)
        except Exception as e:
            print(e)
            pass

        expected_values.append(expected_classification)
        classifier_predictions.append(str(classifier_prediction))
        is_accurate = str(classifier_prediction) == expected_classification
        text_for_csv.append(f"{text_to_classify},{expected_classification},{classifier_prediction},{is_accurate}")

    end_time = time.time()
    execution_time = end_time - start_time

    labels = list(set(expected_values))
    labels.sort()
    accuracy, other_computed_scores = _get_scores_for_classifier(labels, expected_values, classifier_predictions)

    predictions_file = _write_predictions_to_file(text_for_csv, classifier_descriptive_name)
    scores_file = _write_scores_to_file(labels, accuracy, other_computed_scores, classifier_descriptive_name)

    print(f"Accuracy: {round(accuracy * 100, 2)}%")
    print(f"Execution time: {round(execution_time, 4)} seconds")
    print(f"Outputs: {predictions_file}, {scores_file}")

    return


def _get_scores_for_classifier(
    labels: List[str], target_values: List[str], predictions: List[str]
) -> Tuple[float, List[List[float]]]:
    """Compute scores for the classifier"""

    assert len(target_values) == len(predictions)

    accuracy = accuracy_score(target_values, predictions, normalize=True)
    other_computed_scores = precision_recall_fscore_support(
        target_values, predictions, average=None, labels=labels, zero_division=1
    )

    return accuracy, other_computed_scores


def _write_scores_to_file(
    labels: List[str], accuracy: float, other_computed_scores: List[List[float]], file_prefix: str
) -> str:
    """Write the classifier's scores to file
    labels: list of the possible classifications
    accuracy: a float
    other_computed_scores: a 2D array with length 4, one column for each label
    """
    assert len(labels) == len(other_computed_scores[0])

    filename = f"{file_prefix}_{TIMESTAMP}_scores.csv"

    with open(os.path.join(SIMULATIONS_DIR, "outputs", filename), "w") as f:
        f.write(f"# accuracy: {accuracy * 100}%\n")
        f.write("label,precision,recall,fbeta,support\n")

        for i in range(len(labels)):
            precision = round(other_computed_scores[0][i], 4)
            recall = round(other_computed_scores[1][i], 4)
            fscore = round(other_computed_scores[2][i], 4)
            support = round(other_computed_scores[3][i], 4)

            f.write(f"{labels[i]},{precision},{recall},{fscore},{support}\n")
    return filename


def _write_predictions_to_file(lines_to_write: List[str], file_prefix: str) -> str:
    filename = f"{file_prefix}_{TIMESTAMP}.csv"

    os.makedirs(os.path.join(SIMULATIONS_DIR, "outputs"), exist_ok=True)
    with open(os.path.join(SIMULATIONS_DIR, "outputs", filename), "w") as f:
        f.write("text_to_classify,expected_classification,prediction,is_accurate\n")
        f.write("\n".join(lines_to_write))

    return filename


def _get_input_from_file() -> List[List[str]]:
    with open(os.path.join(SIMULATIONS_DIR, INPUT_FILE), "r") as f:
        file_data = f.readlines()
        input_conditions = [i.strip().split(",") for i in file_data if not i.startswith("#") and len(i.split(",")) == 2]

    return input_conditions


if __name__ == "__main__":
    input_data = _get_input_from_file()

    classifiers: List[
        Tuple[
            Callable[
                [
                    str,
                ],
                str,
            ],
            str,
        ]
    ] = [
        (get_classification_from_production_classifier, "production_classifier"),
        (get_respiratory_classification, "respiratory_classification_always"),
        (get_skin_classification, "skin_classifiction_always"),
        # (get_classification_from_ml_classifier, "ml_classifier"),
        # (get_classification_from_stacked_classifier, "stacked"),
        # (get_classification_from_reverse_stacked_classifier, "reverse_stacked"),
    ]

    for classifier_function, descriptive_name in classifiers:
        run_inputs_against_classifier(input_data, classifier_function, descriptive_name)
