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
