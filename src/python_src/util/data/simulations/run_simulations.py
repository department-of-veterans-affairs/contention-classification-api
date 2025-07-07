"""
This script runs a set of input conditions through the classifiers
and outputs their results to file.

The intent is to gather outputs for comparing and tracking behavior of the classifiers.

Usage: (from the codebase root directory)
    poetry run python src/python_src/util/data/simulations/run_simulations.py

"""

import csv
import logging
import os
from datetime import datetime
from typing import List, Tuple

from sklearn.metrics import classification_report

from python_src.util.brd_classification_codes import get_classification_name
from python_src.util.data.simulations.classifiers import (
    BaseClassifierForSimulation,
    MLClassifier,
    ProductionClassifier,
)

SIMULATIONS_DIR = "src/python_src/util/data/simulations/"
INPUT_FILE = "inputs_mini.csv"
TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def _write_metrics_to_file(metrics_report: str, file_prefix: str) -> str:
    filename = f"{file_prefix}_{TIMESTAMP}_metrics.txt"
    with open(os.path.join(SIMULATIONS_DIR, "outputs", filename), "w") as f:
        f.write(metrics_report)
    return filename


def _write_predictions_to_file(
    conditions_to_test: List[str], expected_classifications: List[str], classifier: BaseClassifierForSimulation
) -> str:
    filename = f"{classifier.name.replace(' ', '_')}_{TIMESTAMP}.csv"

    assert len(conditions_to_test) == len(expected_classifications) == len(classifier.predictions)

    os.makedirs(os.path.join(SIMULATIONS_DIR, "outputs"), exist_ok=True)
    with open(os.path.join(SIMULATIONS_DIR, "outputs", filename), "w") as f:
        csv_writer = csv.writer(f, delimiter=",")
        csv_writer.writerow(
            [
                "text_to_classify",
                "expected_code",
                "expected_label",
                "predicted_code",
                "predicted_label",
                "prediction_probability",
                "is_accurate",
            ]
        )

        prediction_probabilities = classifier.prediction_probabilities
        if not prediction_probabilities:
            prediction_probabilities = [1.0] * len(expected_classifications)

        for i in range(len(conditions_to_test)):
            prediction = classifier.predictions[i]
            probability = prediction_probabilities[i]

            csv_writer.writerow(
                [
                    conditions_to_test[i],
                    expected_classifications[i],
                    get_classification_name_from_str_code(expected_classifications[i]),
                    prediction,
                    get_classification_name_from_str_code(prediction),
                    probability,
                    str(expected_classifications[i]) == str(prediction),
                ]
            )

    return filename


def _write_aggregate_predictions_to_file(
    conditions_to_test: List[str],
    expected_classifications: List[str],
    classifiers: List[BaseClassifierForSimulation],
    file_prefix: str,
) -> str:
    """
    Create a csv file that documents the inputs and the predictions across all of the classifiers.

    rows: text_to_classify, expected_classification, model_a_prediction,
     model_a_is_accurate, model_b_prediction, model_b_is_accurate, ...
    """
    filename = f"{file_prefix}_{TIMESTAMP}.csv"

    assert len(conditions_to_test) == len(expected_classifications)

    # build the list of column names and verify that ## verify that the classifiers have the expected number of predictions
    column_names = ["text_to_classify", "expected_code", "expected_label"]
    for c in classifiers:
        assert len(c.predictions) == len(expected_classifications)
        column_names += [f"{c.name}_code", f"{c.name}_label", f"{c.name}_is_accurate"]

    os.makedirs(os.path.join(SIMULATIONS_DIR, "outputs"), exist_ok=True)
    with open(os.path.join(SIMULATIONS_DIR, "outputs", filename), "w") as f:
        csv_writer = csv.writer(f, delimiter=",")
        csv_writer.writerow(column_names)

        for i in range(len(conditions_to_test)):
            row_tokens = [
                conditions_to_test[i],
                expected_classifications[i],
                get_classification_name_from_str_code(expected_classifications[i]),
            ]

            for c in classifiers:
                row_tokens += [
                    c.predictions[i],
                    get_classification_name_from_str_code(c.predictions[i]),
                    c.predictions[i] == expected_classifications[i],
                ]

            csv_writer.writerow(row_tokens)
    return filename


def _get_input_from_file() -> Tuple[List[str], List[str]]:
    conditions_to_test = []
    expected_classifications = []

    with open(os.path.join(SIMULATIONS_DIR, INPUT_FILE), "r") as f:
        csv_reader = csv.reader(f)

        for row in csv_reader:
            if row and row[0].strip().startswith("#"):
                continue
            if len(row) != 2:
                continue

            tokens = [token.strip() for token in row]
            conditions_to_test.append(tokens[0])
            expected_classifications.append(tokens[1])

    return (conditions_to_test, expected_classifications)


def get_classification_name_from_str_code(classification_code: str) -> str:
    classification_name = ""

    if not classification_code or classification_code == "None":
        return classification_name

    try:
        classification_name = get_classification_name(int(classification_code))
    except ValueError:
        logging.warning(f"ValueError getting classification name from [{prediction}]")

    return classification_name


if __name__ == "__main__":
    conditions_to_test, expected_classifications = _get_input_from_file()

    classifiers: List[BaseClassifierForSimulation] = [ProductionClassifier(), MLClassifier()]

    for c in classifiers:
        print(f"---{c.name}---")

        success = c.make_predictions(conditions_to_test)
        if not success:
            raise Exception("mismatch between length of conditions_to_test and predictions")
        predictions_file = _write_predictions_to_file(conditions_to_test, expected_classifications, c)
        labels = list(set(expected_classifications + c.predictions))
        labels.sort()

        metrics_file = _write_metrics_to_file(
            classification_report(
                expected_classifications, c.predictions, labels=labels, target_names=labels, zero_division=1
            ),
            c.name,
        )

        print(f"Outputs: {predictions_file}, {metrics_file}\n")

    if len(classifiers) > 1:
        _write_aggregate_predictions_to_file(
            conditions_to_test, expected_classifications, classifiers, "aggregate_predictions"
        )
