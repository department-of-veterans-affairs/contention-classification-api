"""
Machine Learning Classifier Module for Medical Condition Classification.

This module provides the MLClassifier class which uses a pre-trained ONNX model
and scikit-learn vectorizer to classify medical conditions into standardized
categories. The classifier is specifically designed for VA disability claims
contention classification.

Classes:
    MLClassifier: Main classifier class for medical condition classification.

Example:
    >>> classifier = MLClassifier("model.onnx", "vectorizer.pkl")
    >>> conditions = ["hearing loss", "back pain"]
    >>> predictions = classifier.make_predictions(conditions)
    >>> print(predictions)
    [('Hearing Loss', 0.95), ('Musculoskeletal - Back', 0.88)]
"""

import logging
import os
import re
import string
from typing import Dict, List

import joblib
import onnxruntime as ort
from numpy import float32, ndarray


class MLClassifier:
    """
    Machine Learning classifier for medical condition classification.

    This class loads a pre-trained ONNX model and corresponding vectorizer to
    classify medical conditions and contentions into standardized categories
    for VA disability claims processing.

    Attributes:
        session (ort.InferenceSession): ONNX Runtime inference session for the model.
        vectorizer: Scikit-learn vectorizer for text preprocessing.

    Args:
        model_file (str): Path to the ONNX model file.
        vectorizer_file (str): Path to the pickled vectorizer file.

    Raises:
        Exception: If either the model file or vectorizer file is not found.

    Example:
        >>> classifier = MLClassifier("model.onnx", "vectorizer.pkl")
        >>> predictions = classifier.make_predictions(["hearing loss"])
        >>> print(predictions[0])
        ('Hearing Loss', 0.95)
    """

    def __init__(self, model_file: str = "", vectorizer_file: str = ""):
        """
        Initialize the MLClassifier with model and vectorizer files.

        Args:
            model_file (str): Path to the ONNX model file. Defaults to empty string.
            vectorizer_file (str): Path to the vectorizer pickle file. Defaults to empty string.

        Raises:
            Exception: If either file does not exist.
        """
        if not os.path.exists(model_file):
            raise Exception(f"File not found: {model_file}")
        if not os.path.exists(vectorizer_file):
            raise Exception(f"File not found: {vectorizer_file}")
        self.session = ort.InferenceSession(model_file)
        self.vectorizer = joblib.load(vectorizer_file)

    def make_predictions(self, conditions: list[str]) -> List[tuple[str, float]]:
        """
        Classify a list of medical conditions into standardized categories.

        Takes a list of condition descriptions and returns predicted classifications
        with their confidence probabilities. Each condition is cleaned, vectorized,
        and passed through the trained model for classification.

        Args:
            conditions (list[str]): List of condition descriptions to classify.
                Example: ["numbness in right arm", "ringing noise in ears"]

        Returns:
            List[tuple[str, float]]: List of tuples containing the predicted
                classification name and probability for each condition.
                Example: [('Musculoskeletal - Wrist', 0.95), ('Hearing Loss', 0.88)]

        Note:
            If an error occurs during prediction, returns error tuples with
            ("error", 0.0) for each condition.
        """
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
        """
        Get the output names from the ONNX model session.

        Returns:
            list[str]: List of output node names from the ONNX model.
        """
        return [i.name for i in self.session.get_outputs()]

    def get_inputs_for_session(self, conditions: list[str]) -> Dict[str, ndarray]:
        """
        Transform condition text into model input format.

        Applies the loaded vectorizer to transform text conditions into
        numerical features that can be fed to the ONNX model.

        Args:
            conditions (list[str]): List of condition descriptions to transform.

        Returns:
            Dict[str, ndarray]: Dictionary mapping input node names to
                transformed feature arrays in float32 format.
        """
        transformed_inputs = self.vectorizer.transform(conditions)
        return {self.session.get_inputs()[0].name: transformed_inputs.toarray().astype(float32)}

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text for model input.

        Performs standard text preprocessing including:
        - Converting to lowercase
        - Removing punctuation
        - Normalizing whitespace
        - Trimming leading/trailing spaces

        Args:
            text (str): Raw text to clean.

        Returns:
            str: Cleaned and normalized text.

        Example:
            >>> classifier.clean_text("HEARING LOSS!!!")
            'hearing loss'
        """
        text = text.lower()
        text = re.sub(rf"[{re.escape(string.punctuation)}]", "", text)
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text
