import os
from typing import List

import joblib

from python_src.util.app_utilities import app_config
from python_src.util.brd_classification_codes import get_classification_code


class MLClassifier:

    def __init__(self, model_file: str):
        if not os.path.exists(model_file):
            raise Exception(f"File not found: {model_file}")
        self.model = joblib.load(model_file)
    
    def make_predictions(self, conditions: list[str]) -> List[str]:
        """Returns a list of the predicted classification names, for example:
        ['Musculoskeletal - Wrist', 'Eye (Vision)', 'Hearing Loss']
        """
        return [str(c) or "no-classification" for c in self.model.predict(conditions)]


if __name__ == "__main__":

    # usage: python -W "ignore" src/python_src/util/ml_classifier.py

    ml_classifier = MLClassifier(app_config["ml_classifier"]["model_file"] )
    
    sample_test_cases = [
        "numbness in right lower arm",
        "loss of hearing in both ears",
        "post traumatic stress disorder",
        "tendonitis in right shoulder",
        "generalized anxiety disorder",
        "blurry/double vision at night",
        "chronic ringing noise in ears",
        "arthritis in right wrist"
        ]

    predictions = ml_classifier.make_predictions(sample_test_cases)
    predictions_as_codes = [str(get_classification_code(i)) or 'no-classification' for i in predictions]
    
    for i in range(len(sample_test_cases)):
        print(f"{sample_test_cases[i]}\t{predictions_as_codes[i]}\t{predictions[i]}")

    print("done")
