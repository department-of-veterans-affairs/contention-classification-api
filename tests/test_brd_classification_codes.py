"""Tests for the BRD classification codes module."""

import json
from typing import Any, Dict, List
from unittest.mock import mock_open, patch

import pytest
from fastapi.testclient import TestClient

from src.python_src.util.brd_classification_codes import (
    CLASSIFICATION_CODES_BY_NAME,
    CLASSIFICATION_NAMES_BY_CODE,
    get_classification_code,
    get_classification_name,
    get_classification_names_by_code,
)


def test_get_classification_names_by_code(test_client: TestClient) -> None:
    """Test get_classification_names_by_code with mock data."""
    mock_data: Dict[str, List[Dict[str, Any]]] = {
        "items": [
            {"id": 8989, "name": "Mental Disorders"},
            {"id": 8997, "name": "Musculoskeletal - Knee"},
            {"id": 3140, "name": "Hearing Loss"},
        ]
    }
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
        result = get_classification_names_by_code()
        assert result == {
            8989: "Mental Disorders",
            8997: "Musculoskeletal - Knee",
            3140: "Hearing Loss",
        }


def test_get_classification_names_by_code_missing_items(test_client: TestClient) -> None:
    """Test handling when JSON doesn't have 'items' key."""
    mock_data: Dict[str, List[Dict[str, Any]]] = {"wrong_key": []}
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
        with pytest.raises(KeyError):
            get_classification_names_by_code()


def test_get_classification_names_by_code_invalid_json(test_client: TestClient) -> None:
    """Test handling of invalid JSON data."""
    with patch("builtins.open", mock_open(read_data="invalid json")):
        with pytest.raises(json.JSONDecodeError):
            get_classification_names_by_code()


def test_get_classification_name(test_client: TestClient) -> None:
    """Test get_classification_name with mock data."""
    mock_data: Dict[str, List[Dict[str, Any]]] = {
        "items": [
            {"id": 8989, "name": "Mental Disorders"},
            {"id": 8997, "name": "Musculoskeletal - Knee"},
            {"id": 3140, "name": "Hearing Loss"},
        ]
    }
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
        assert get_classification_name(8989) == "Mental Disorders"
        assert get_classification_name(8997) == "Musculoskeletal - Knee"
        assert get_classification_name(3140) == "Hearing Loss"
        assert get_classification_name(9999) is None


def test_get_classification_code(test_client: TestClient) -> None:
    """Test get_classification_name with mock data."""
    mock_data: Dict[str, List[Dict[str, Any]]] = {
        "items": [
            {"id": 8989, "name": "Mental Disorders"},
            {"id": 8997, "name": "Musculoskeletal - Knee"},
            {"id": 3140, "name": "Hearing Loss"},
        ]
    }
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
        assert get_classification_code("Mental Disorders") == 8989
        assert get_classification_code("Musculoskeletal - Knee") == 8997
        assert get_classification_code("Hearing Loss") == 3140
        assert get_classification_code("lorem ipsum") is None


def test_get_classification_names_by_code_file_error(test_client: TestClient) -> None:
    """Test error handling when file cannot be opened."""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        with pytest.raises(FileNotFoundError):
            get_classification_names_by_code()


def test_get_classification_name_file_error(test_client: TestClient) -> None:
    """Test error handling when file cannot be opened."""
    with patch.dict(CLASSIFICATION_NAMES_BY_CODE, {}, clear=True):
        result = get_classification_name(8989)
        assert result is None


def test_get_classification_code_file_error(test_client: TestClient) -> None:
    """Test error handling when file cannot be opened."""
    with patch.dict(CLASSIFICATION_CODES_BY_NAME, {}, clear=True):
        result = get_classification_code("lorem ipsum")
        assert result is None


def test_get_classification_code_with_endDateTime() -> None:
    mock_data = {
        "items": [
            {"id": 8989, "name": "Mental Disorders"},
            {"id": 8997, "name": "Musculoskeletal - Knee", "endDateTime": None},
            {"id": 3140, "name": "Hearing Loss", "endDateTime": "2036-03-20T00:11:43Z"},
            {"id": 8968, "name": "Digestive", "endDateTime": "2016-03-20T00:11:43Z"},
            {"id": 9999, "name": "Test", "endDateTime": "2016-03-20"},
        ]
    }
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
        dict_of_codes = get_classification_names_by_code()
        assert dict_of_codes.get(8989) == "Mental Disorders"
        assert dict_of_codes.get(8997) == "Musculoskeletal - Knee"
        assert dict_of_codes.get(3140) == "Hearing Loss"
        assert dict_of_codes.get(8968) is None
        assert dict_of_codes.get(9999) is None
