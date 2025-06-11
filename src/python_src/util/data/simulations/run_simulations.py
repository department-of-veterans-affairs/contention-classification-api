"""
This script runs a set of input conditions through the classifiers
and outputs their results to file. 

The intent is to gather outputs that allow for comparing performance of the classifiers.


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


Usage:
    poetry run python src/python_src/util/data/simulations/run_simulations.py

"""
import os
import random
import time
from datetime import datetime

from python_src.util.app_utilities import expanded_lookup_table

SIMULATIONS_DIR = "src/python_src/util/data/simulations/"
INPUT_FILE = "inputs.csv"
TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


## start of classifiers ###
def get_classification_from_production_classifier(condition_text):
    try:
        return expanded_lookup_table.get(condition_text).get("classification_code")
    except Exception:
        pass

def get_classification_from_ml_classifier(condition_text):
    ## TODO : replace this when we have the ML classifier running locally
    return random.choice([None, 8968, 8973, 8979, 8989, 8997, 9004, 9007, 9016])

def get_classification_from_stacked_classifier(condition_text):
    classification = get_classification_from_production_classifier(condition_text)
    if not classification:
        classification = get_classification_from_ml_classifier(condition_text)
    return classification

def get_classification_from_reverse_stacked_classifier(condition_text):
    classification = get_classification_from_ml_classifier(condition_text)
    if not classification:
        classification = get_classification_from_production_classifier(condition_text)
    return classification
## end of classifiers ###


def run_inputs_against_classifier(input_data, classifier_function, short_descriptive_name):
    print(f"\n--- {short_descriptive_name} -------")
    start_time = time.time()
    output_data = []
    accurate_predictions = 0

    for text_to_classify, expected_classification in input_data:
        classifier_prediction = None
        is_accurate = False
        try:
            classifier_prediction = classifier_function(text_to_classify)
            if classifier_prediction and str(classifier_prediction) == expected_classification:
                accurate_predictions += 1
        except Exception:
            pass

        output_data.append(f"{text_to_classify},{expected_classification},{classifier_prediction},{is_accurate}")

    end_time = time.time()
    execution_time = end_time - start_time

    output_file = _write_lines_to_file(output_data, f"{short_descriptive_name}_{TIMESTAMP}.csv")

    print(f"Accuracy: {accurate_predictions} of {len(input_data)} ({round(accurate_predictions/len(input_data), 2) * 100}%)")
    print(f"Execution time: {round(execution_time, 4)} seconds")
    print(f"Output file: {output_file}")

    return


def _write_lines_to_file(lines_to_write, filename):
    os.makedirs(os.path.join(SIMULATIONS_DIR, "outputs"), exist_ok=True)
    with open(os.path.join(SIMULATIONS_DIR, "outputs", filename), 'w') as f:
        f.write("text_to_classify,expected_classification,prediction,is_accurate\n")
        f.write("\n".join(lines_to_write))

    return filename

def _get_input_from_file():
    with open(os.path.join(SIMULATIONS_DIR, INPUT_FILE), 'r') as f:
        file_data = f.readlines()
        input_conditions = [i.strip().split(",") for i in file_data if not i.startswith("#") and len(i.split(","))==2]

    return input_conditions

if __name__ == "__main__":

    input_data = _get_input_from_file()

    classifiers = [ 
        (get_classification_from_production_classifier, "production_classifier"),
        (get_classification_from_ml_classifier, "ml_classifier"),
        (get_classification_from_stacked_classifier, "stacked"),
        (get_classification_from_reverse_stacked_classifier, "reverse_stacked"),
    ]

    for classifier_function, descriptive_name in classifiers:
        run_inputs_against_classifier(input_data, classifier_function, descriptive_name)
