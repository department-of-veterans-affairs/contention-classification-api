import logging
import os
import re
import string
from typing import Dict, List

import joblib
import onnxruntime as ort
from numpy import float32, ndarray


class MLClassifier:
    def __init__(self, model_file: str = "", vectorizer_file: str = ""):

        if not os.path.exists(model_file):
            raise Exception(f"File not found: {model_file}")
        if not os.path.exists(vectorizer_file):
            raise Exception(f"File not found: {vectorizer_file}")
        self.session = ort.InferenceSession(model_file)
        self.vectorizer = joblib.load(vectorizer_file)


    def make_predictions(self, conditions: list[str]) -> List[tuple[str, float]]:
        """Returns a list of the predicted classification names with probabilities, for example:
        [('Musculoskeletal - Wrist', 0.95), ('Eye (Vision)', 0.88), ('Hearing Loss', 0.92)]
        arg conditions: a list of strings, each element
                        representing a condition to be classified. for example,
                        ["numbness in right arm", "ringing noise in ears",
                        "asthma", "generalized anxiety disorder"]
        """

        predictions = [("error", 0.0)] * len(conditions)

        try:
            cleaned_conditions = [self.clean_text(c) for c in conditions]
            outputs = self.session.run(self.get_outputs_for_session(), self.get_inputs_for_session(cleaned_conditions))
            labels = outputs[0]
            probabilities = outputs[1]

            predictions = [(labels[i], probabilities[i][labels[i]]) for i in range(len(labels))]
        except Exception as e:
            logging.error(e)
        return predictions

    def get_outputs_for_session(self) -> list[str]:
        return [i.name for i in self.session.get_outputs()]

    def get_inputs_for_session(self, conditions: list[str]) -> Dict[str, ndarray]:
        transformed_inputs = self.vectorizer.transform(conditions)
        return {self.session.get_inputs()[0].name: transformed_inputs.toarray().astype(float32)}

    def clean_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(rf"[{re.escape(string.punctuation)}]", "", text)
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text
