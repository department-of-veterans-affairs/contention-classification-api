from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from pytest import MonkeyPatch


def test_health_check_success(test_client: TestClient, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("src.python_src.api.dc_lookup_table", {"key1": "value:1"})
    monkeypatch.setattr("src.python_src.api.dropdown_lookup_table", {"key2": "value:2"})
    monkeypatch.setattr("src.python_src.api.expanded_lookup_table", {"key3": "value:3"})
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_check_empty_dc_lookup(test_client: TestClient, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("src.python_src.api.dc_lookup_table", {})
    monkeypatch.setattr("src.python_src.api.dropdown_lookup_table", {"key2": "value:2"})
    monkeypatch.setattr("src.python_src.api.expanded_lookup_table", {"key3": "value:3"})
    response = test_client.get("/health")
    assert response.status_code == 500
    assert response.json() == {"detail": "DC Lookup table is empty"}


def test_health_check_empty_expanded_lookup(test_client: TestClient, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("src.python_src.api.dc_lookup_table", {})
    monkeypatch.setattr("src.python_src.api.dropdown_lookup_table", {})
    monkeypatch.setattr("src.python_src.api.expanded_lookup_table", {"key3": "value:3"})
    response = test_client.get("/health")
    assert response.status_code == 500
    assert response.json() == {"detail": "DC Lookup, Contention Text Lookup tables are empty"}


def test_health_check_empty_contention_text_lookup(test_client: TestClient, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("src.python_src.api.dc_lookup_table", {})
    monkeypatch.setattr("src.python_src.api.dropdown_lookup_table", {})
    monkeypatch.setattr("src.python_src.api.expanded_lookup_table", {})
    response = test_client.get("/health")
    assert response.status_code == 500
    assert response.json() == {"detail": "DC Lookup, Expanded Lookup, Contention Text Lookup tables are empty"}


@patch("boto3.client")
def test_ml_health_check(mock_boto3_client: Mock, test_client: TestClient, monkeypatch: MonkeyPatch) -> None:
    mock_boto3_client.get_caller_identity.return_value = {"Arn": "arn-value"}
    monkeypatch.setattr("src.python_src.api.ml_classifier", "not-none")
    response = test_client.get("/health-ml-classifier")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch("boto3.client")
def test_ml_health_check_ml_classifier_not_defined(mock_boto3_client: Mock, test_client: TestClient, \
        monkeypatch: MonkeyPatch) -> None:
    mock_boto3_client.get_caller_identity.return_value = {"Arn": "arn-value"}
    monkeypatch.setattr("src.python_src.api.ml_classifier", None)
    response = test_client.get("/health-ml-classifier")
    assert response.status_code == 500
    assert response.json() == {"detail": "ML Classifier is not initialized"}

@patch("boto3.client")
def test_ml_health_check_aws_sts_exception(mock_boto3_client: Mock, test_client: TestClient, monkeypatch: MonkeyPatch) -> None:
    mock_boto3_client.side_effect = Exception()
    monkeypatch.setattr("src.python_src.api.ml_classifier", "not-none")
    response = test_client.get("/health-ml-classifier")
    assert response.status_code == 500
    assert response.json() == {"detail": "Undefined AWS STS caller identity"}

@patch("boto3.client")
def test_ml_health_check_aws_sts_and_ml_classifier_errors(mock_boto3_client: Mock, test_client: TestClient, 
    monkeypatch: MonkeyPatch) -> None:
    mock_boto3_client.side_effect = Exception()
    monkeypatch.setattr("src.python_src.api.ml_classifier", None)
    response = test_client.get("/health-ml-classifier")
    assert response.status_code == 500
    assert response.json() == {"detail": "ML Classifier is not initialized, Undefined AWS STS caller identity"}
