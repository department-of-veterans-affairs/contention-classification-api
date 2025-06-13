"""
This script runs a set of input conditions through the classifiers
and outputs their results to file.

The intent is to gather outputs for comparing and tracking behavior of the classifiers.

Usage: (from the codebase root directory)
    poetry run python src/python_src/util/data/simulations/run_simulations.py

"""

import os
from datetime import datetime
from typing import List, Tuple

from sklearn.metrics import classification_report

from python_src.util.data.simulations.classifiers import (
    BaseClassifierForSimulation,
    ProductionClassifier,
    RespiratoryClassifier,
)

SIMULATIONS_DIR = "src/python_src/util/data/simulations/"
INPUT_FILE = "inputs_mini.csv"
TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def _write_scores_to_file(classification_report: str, file_prefix: str) -> str:
    filename = f"{file_prefix}_{TIMESTAMP}_scores.txt"

    with open(os.path.join(SIMULATIONS_DIR, "outputs", filename), "w") as f:
        f.writelines(classification_report)
    return filename


def _write_predictions_to_file(
    conditions_to_test: List[str], expected_classifications: List[str], predictions: List[str], file_prefix: str
) -> str:
    filename = f"{file_prefix}_{TIMESTAMP}.csv"

    assert len(conditions_to_test) == len(expected_classifications) == len(predictions)

    os.makedirs(os.path.join(SIMULATIONS_DIR, "outputs"), exist_ok=True)
    with open(os.path.join(SIMULATIONS_DIR, "outputs", filename), "w") as f:
        # initial row: columns
        f.write("text_to_classify,expected_classification,prediction,is_accurate\n")

        for i in range(len(conditions_to_test)):
            prediction = conditions_to_test[i]
            f.write(
                f"{conditions_to_test[i]},{expected_classifications[i]},{prediction},{
                    str(expected_classifications[i]) == str(prediction)
                }\n"
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
     is_model_a_accurate, model_b_prediction, is_model_b_accurate, ...
    """
    filename = f"{file_prefix}_{TIMESTAMP}.csv"

    assert len(conditions_to_test) == len(expected_classifications)

    # build the list of column names and verify that ## verify that the classifiers have the expected number of predictions
    column_names = ["text_to_classify", "expected_classification"]
    for c in classifiers:
        assert len(c.predictions) == len(expected_classifications)
        column_names += [c.name, f"{c.name} accurate?"]

    os.makedirs(os.path.join(SIMULATIONS_DIR, "outputs"), exist_ok=True)
    with open(os.path.join(SIMULATIONS_DIR, "outputs", filename), "w") as f:
        f.write(f"{','.join(column_names)}\n")

        for i in range(len(conditions_to_test)):
            row_to_write = f"{conditions_to_test[i]},{expected_classifications[i]}"

            for c in classifiers:
                row_to_write += f",{c.predictions[i]},{c.predictions[i] == expected_classifications[i]}"

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

    classifiers: List[BaseClassifierForSimulation] = [ProductionClassifier(), RespiratoryClassifier()]

    for c in classifiers:
        print(f"---{c.name}---")

        c.make_predictions(conditions_to_test)

        predictions_file = _write_predictions_to_file(conditions_to_test, expected_classifications, c.predictions, c.name)

        print(c.predictions)
        computed_scores = classification_report(expected_classifications, c.predictions, target_names=labels, zero_division=1)

        scores_file = _write_scores_to_file(computed_scores, c.name)

        print(f"Outputs: {predictions_file}, {scores_file}\n")

    if len(classifiers) > 1:
        _write_aggregate_predictions_to_file(
            conditions_to_test, expected_classifications, classifiers, "aggregate_predictions"
        )
