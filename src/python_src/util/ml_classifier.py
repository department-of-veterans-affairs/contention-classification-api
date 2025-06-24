import logging
import os
from numpy import float32
import onnxruntime as ort
from typing import List

import joblib


class MLClassifier:
    def __init__(self, model_file: str, vectorizer_file: str):
        if not os.path.exists(model_file):
            raise Exception(f"File not found: {model_file}")
        if not os.path.exists(vectorizer_file):
            raise Exception(f"File not found: {vectorizer_file}")
        self.session = ort.InferenceSession(model_file)
        self.vectorizer = joblib.load(vectorizer_file)

    def make_predictions(self, conditions: list[str]) -> List[str]:
        """Returns a list of the predicted classification names, for example:
        ['Musculoskeletal - Wrist', 'Eye (Vision)', 'Hearing Loss']

        arg conditions: a list of strings, each element
                        representing a condition to be classified. for example,
                        ["numbness in right arm", "ringing noise in ears",
                        "asthma", "generalized anxiety disorder"]
        """

        try:
            transformed_value_to_test = self.vectorizer.transform(conditions).toarray().astype(float32)
            output_names = [self.session.get_outputs()[0].name]
            input_name = self.session.get_inputs()[0].name
            predictions = self.session.run(output_names, {input_name: transformed_value_to_test})
        except Exception as e:
            logging.error(e)
            predictions = ['error']*len(conditions)
        return predictions


        