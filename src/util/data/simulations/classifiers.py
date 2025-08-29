from typing import List

from ...app_utilities import expanded_lookup_table, ml_classifier
from ...brd_classification_codes import get_classification_code


class BaseClassifierForSimulation:
    name: str
    predictions: List[str] = []
    prediction_probabilities: List[float] = []

    def make_predictions(self, conditions: List[str]) -> bool:
        """
        returns True if the count of predictions matches the count
        of input conditions
        """
        return True


class ProductionClassifier(BaseClassifierForSimulation):
    name = "csv_lookup"

    def make_predictions(self, conditions: List[str]) -> bool:
        predicted_classifications: List[str] = []
        for condition in conditions:
            try:
                prediction = str(expanded_lookup_table.get(condition).get("classification_code"))
            except Exception as e:
                print("error: ", e)

            predicted_classifications.append(prediction)
        self.predictions = predicted_classifications
        return len(self.predictions) == len(conditions)


class MLClassifier(BaseClassifierForSimulation):
    name = "ml_classifier"

    def make_predictions(self, conditions: List[str]) -> bool:
        if ml_classifier is None:
            return False
        classifier_output = ml_classifier.make_predictions(conditions)
        predicted_labels = [i[0] for i in classifier_output]
        self.predictions = [str(get_classification_code(label)) for label in predicted_labels]
        self.prediction_probabilities = [round(i[1], 2) for i in classifier_output]

        return len(self.predictions) == len(conditions)


class RespiratoryClassifier(BaseClassifierForSimulation):
    """For demo purposes: a classifier that always predicts a classification
    of respiratory, which maps to classification code '9012'"""

    name = "respiratory_classifier"

    def make_predictions(self, conditions: List[str]) -> bool:
        self.predictions = ["9012"] * len(conditions)
        return len(self.predictions) == len(conditions)
