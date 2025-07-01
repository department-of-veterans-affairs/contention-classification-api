from unittest.mock import MagicMock, patch

from src.python_src.util.data.simulations.classifiers import MLClassifier, ProductionClassifier, RespiratoryClassifier


@patch("src.python_src.util.data.simulations.classifiers.ml_classifier")
def test_ml_classifier(mock_ml_classifier: MagicMock) -> None:
    mock_ml_classifier.make_predictions.return_value = ["Respiratory", "Skin", "Digestive"]

    ml_classifier = MLClassifier()
    assert ml_classifier.name == "ml_classifier"
    ml_classifier.make_predictions(["asthma", "acne", "gallstones"])
    assert ml_classifier.predictions == ["9012", "9016", "8968"]


def test_production_classifier() -> None:
    production_classifier = ProductionClassifier()
    assert production_classifier.name == "csv_lookup"
    production_classifier.make_predictions(["asthma", "acne", "gallstones"])
    assert production_classifier.predictions == ["9012", "9016", "8968"]
    production_classifier.make_predictions(["lorem", "ipsun", "dolor", "donut", "cookie"])
    assert production_classifier.predictions == ["None"] * 5


def test_respiratory_classifier() -> None:
    respiratory_classifier = RespiratoryClassifier()
    assert respiratory_classifier.name == "respiratory_classifier"
    respiratory_classifier.make_predictions(["asthma", "acne", "gallstones"])
    assert respiratory_classifier.predictions == ["9012", "9012", "9012"]
    respiratory_classifier.make_predictions(["lorem", "ipsun", "dolor", "donut", "cookie"])
    assert respiratory_classifier.predictions == ["9012", "9012", "9012", "9012", "9012"]
