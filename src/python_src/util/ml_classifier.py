import logging
import os
import re
import string
from typing import Any, Dict, List

import boto3
import joblib
import onnxruntime as ort
from numpy import float32, ndarray

from src.python_src.util import app_utilities


class MLClassifier:
    def __init__(self, model_file: str = "", vectorizer_file: str = "", model_directory_path: str = ""):
        model_file, vectorizer_file, model_directory_path = self.download_models_from_s3(
            model_file, vectorizer_file, model_directory_path
        )

        if not os.path.exists(model_file):
            raise Exception(f"File not found: {model_file}")
        if not os.path.exists(vectorizer_file):
            raise Exception(f"File not found: {vectorizer_file}")
        self.session = ort.InferenceSession(model_file)
        self.vectorizer = joblib.load(vectorizer_file)

    def download_models_from_s3(
        self, model_file: str = "", vectorizer_file: str = "", model_directory_path: str = ""
    ) -> tuple[str, str, str]:
        if not model_directory_path:
            model_directory_path = app_utilities.app_config["ml_classifier"]["data"]["directory"]
        os.makedirs(model_directory_path, exist_ok=True)
        if not model_file:
            model_file = app_utilities.app_config["ml_classifier"]["model_file"]
        if not vectorizer_file:
            vectorizer_file = app_utilities.app_config["ml_classifier"]["vectorizer_file"]
        try:
            s3_client = boto3.client("s3")
            s3_client.download_file(
                app_utilities.app_config["ml_classifier"]["aws"]["bucket"],
                app_utilities.app_config["ml_classifier"]["aws"]["model"],
                model_file,
            )
            s3_client.download_file(
                app_utilities.app_config["ml_classifier"]["aws"]["bucket"],
                app_utilities.app_config["ml_classifier"]["aws"]["model"],
                vectorizer_file,
            )
        except Exception as e:
            print(e)
        return model_file, vectorizer_file, model_directory_path

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
