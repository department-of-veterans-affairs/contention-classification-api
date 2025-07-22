import logging
import os
import re
import string
from typing import Any, Dict, List

import app_utilities
import boto3
import joblib
import onnxruntime as ort
from numpy import float32, ndarray


class MLClassifier:
    def __init__(self, model_file: str, vectorizer_file: str):
        app_config = app_utilities.load_config(os.path.join(os.path.dirname(__file__), "app_config.yaml"))
        model_path = ""
        if not os.path.exists(model_path):
            os.makedirs(model_path)
        try:
            s3_client = boto3.client("s3")
            s3_client.download_file(
                Bucket=app_config["ml_classifier"]["aws"]["bucket"],
                Key=app_config["ml_classifier"]["aws"]["model"],
                Filename=app_config["ml_classifier"]["model_file"],
            )
            s3_client.download_file(
                Bucket=app_config["ml_classifier"]["aws"]["bucket"],
                Key=app_config["ml_classifier"]["aws"]["vectorizer"],
                Filename=app_config["ml_classifier"]["vectorizer_file"],
            )
        except Exception as e:
            print(e)
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
        predictions = ["error"] * len(conditions)
        try:
            cleaned_conditions = [self.clean_text(c) for c in conditions]
            outputs = self.session.run(self.get_outputs_for_session(), self.get_inputs_for_session(cleaned_conditions))
            predictions = outputs[0]
        except Exception as e:
            logging.error(e)
        return predictions

    def get_outputs_for_session(self) -> list[str]:
        return [self.session.get_outputs()[0].name]

    def get_inputs_for_session(self, conditions: list[str]) -> Dict[str, ndarray]:
        transformed_inputs = self.vectorizer.transform(conditions)

        return {self.session.get_inputs()[0].name: transformed_inputs.toarray().astype(float32)}

    def clean_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(rf"[{re.escape(string.punctuation)}]", "", text)
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text
