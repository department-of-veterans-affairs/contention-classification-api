import pickle
from typing import Any, List

from python_src.util.app_utilities import app_config
from python_src.util.brd_classification_codes import get_classification_code


class MLClassifier:

    def __init__(self, features_file: str, model_file: str):
        self.loaded_model = pickle.load(open(model_file, 'rb'))
        self.x_test = pickle.load(open(features_file, 'rb'))
     
    def make_predictions(self, conditions: list[str]) -> List[str] | Any:
        return self.loaded_model.predict(conditions).astype(str).tolist()
        
if __name__ == "__main__":

    # usage: python -W "ignore" src/python_src/util/ml_classifier.py

    ml_classifier = MLClassifier(
        app_config["ml_classifier"]["features_file"],
        app_config["ml_classifier"]["model_file"] )
    
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