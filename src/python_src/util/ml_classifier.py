import os
from typing import List

import joblib


class MLClassifier:
    def __init__(self, model_file: str):
        if not os.path.exists(model_file):
            raise Exception(f"File not found: {model_file}")
        self.model = joblib.load(model_file)

    def make_predictions(self, conditions: list[str]) -> List[str]:
        """Returns a list of the predicted classification names, for example:
        ['Musculoskeletal - Wrist', 'Eye (Vision)', 'Hearing Loss']

        arg conditions: a list of strings, each element
                        representing a condition to be classified. for example,
                        ["numbness in right arm", "ringing noise in ears",
                        "asthma", "generalized anxiety disorder"]
        """
        return [str(c) or "no-classification" for c in self.model.predict(conditions)]
