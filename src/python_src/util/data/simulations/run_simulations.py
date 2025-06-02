"""
Proof of concept: a standalone script that runs a set of input conditions through 
stubbed versions of the classifiers and outputs their results to file. 

This is meant for demo purposes only. Among other issues: the outputs may not be 
representative of the classifiers, and the implementation will not support large data sets. 


Usage:
    poetry run python src/python_src/util/data/simulations/run_simulations.py

"""
from datetime import datetime
import os
import time

from python_src.util.app_utilities import expanded_lookup_table
from python_src.util.ml_classifier import ml_classify_text
from python_src.util.classifier_utilities import get_classification_code_name


SIMULATIONS_DIR = "src/python_src/util/data/simulations/"
INPUT_FILE = "input_01.csv"
TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")



## start of sample classifiers, for demo purposes only ###
def get_classification_from_production_classifier(condition_text):
    try:
        return expanded_lookup_table.get(condition_text).get("classification_code")
    except Exception as e:
        pass

def get_classification_from_ml_classifier(condition_text):
    return ml_classify_text(condition_text)

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
## end of stubbed classifiers ###


def run_inputs_against_classifier(input_data, classifier_function, short_descriptive_name):
    print(f"--- {short_descriptive_name} -------")
    start_time = time.time()
    output_data = []
    matches = 0

    for condition_text, expected_code in input_data:
        
        classifier_decision = None
        is_match = False
        try:
            classifier_decision = classifier_function(condition_text)
            is_match = str(classifier_decision)== expected_code
            if is_match:
                matches += 1
        except Exception as e:
            pass

        output_data.append(f"{condition_text},{classifier_decision},{is_match}")

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {round(execution_time, 4)} seconds")
    print(f"Matches: {round(matches / len(input_data), 2) * 100}%")
    _write_lines_to_file(output_data, f"{short_descriptive_name}_{TIMESTAMP}.csv")
    print("\n\n")

    return


def _write_lines_to_file(lines_to_write, filename):
    os.makedirs(os.path.join(SIMULATIONS_DIR, "outputs"), exist_ok=True)
    with open(os.path.join(SIMULATIONS_DIR, "outputs", filename), 'w') as f:
        f.write("input,model_result,is_match\n")
        f.write("\n".join(lines_to_write))

    print(f"wrote {filename}")

def _get_input_from_file():
    with open(os.path.join(SIMULATIONS_DIR, INPUT_FILE), 'r') as f:
        file_data = f.readlines()
        input_conditions = [i.strip().split(",") for i in file_data if len(i.split(","))==2]

    print(f"length of inputs: {len(input_conditions)}")
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
