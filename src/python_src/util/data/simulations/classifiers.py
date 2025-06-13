from typing import List

from python_src.util.app_utilities import expanded_lookup_table

class BaseClassifierForSimulation:
    name: str
    predictions: List[str]

    def make_predictions(self, conditions: List[str]) -> None:
        pass


class ProductionClassifier(BaseClassifierForSimulation):
    name = "csv lookup"

    def make_predictions(self, conditions: List[str]) -> None:
        predicted_classifications: List[str] = []
        for condition in conditions:
            try:
                prediction = str(expanded_lookup_table.get(condition).get("classification_code"))
            except Exception as e:
                print("error: ", e)
                prediction = "no-classification"

            predicted_classifications.append(prediction)
        self.predictions = predicted_classifications


class RespiratoryClassifier(BaseClassifierForSimulation):
    """For demo purposes: a classifier that always predicts the label '9012' (classification: respiratory)"""

    name = "respiratory classifier"

    def make_predictions(self, conditions: List[str]) -> None:
        self.predictions = ["9016"] * len(conditions)
