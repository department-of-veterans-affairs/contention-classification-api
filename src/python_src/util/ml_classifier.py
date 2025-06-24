import logging
import os
from typing import Any, Dict, List

import joblib
import onnxruntime as ort
from numpy import float32, ndarray


class MLClassifier:
    def __init__(self, model_file: str, vectorizer_file: str):
        if not os.path.exists(model_file):
            raise Exception(f"File not found: {model_file}")
        if not os.path.exists(vectorizer_file):
            raise Exception(f"File not found: {vectorizer_file}")
        self.session = ort.InferenceSession(model_file)
        self.vectorizer = joblib.load(vectorizer_file)

    def make_predictions(self, conditions: list[str]) -> List[str] | Any:
        """Returns a list of the predicted classification names, for example:
        ['Musculoskeletal - Wrist', 'Eye (Vision)', 'Hearing Loss']

        arg conditions: a list of strings, each element
                        representing a condition to be classified. for example,
                        ["numbness in right arm", "ringing noise in ears",
                        "asthma", "generalized anxiety disorder"]
        """
        try:
            predictions = self.session.run(self.get_outputs_for_session(), self.get_inputs_for_session(conditions))
        except Exception as e:
            logging.error(e)
            predictions = ["error"] * len(conditions)
        return predictions

    def get_outputs_for_session(self) -> list[str]:
        return [self.session.get_outputs()[0].name]

    def get_inputs_for_session(self, conditions: list[str]) -> Dict[str, ndarray]:
        transformed_inputs = self.vectorizer.transform(conditions)

        return {self.session.get_inputs()[0].name: transformed_inputs.toarray().astype(float32)}
