"""Tests for the BRD classification codes module."""

import json
from typing import Any, Dict, List
from unittest.mock import mock_open, patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.python_src.util.brd_classification_codes import (
    CLASSIFICATION_CODES_BY_NAME,
    CLASSIFICATION_NAMES_BY_CODE,
    get_classification_code,
    get_classification_name,
    get_classification_names_by_code,
    get_classification,
    CLASSIFICATION_CODES_BY_ID
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


@patch("src.python_src.util.brd_classification_codes.get_classification_by_code")
@patch("src.python_src.util.brd_classification_codes.CLASSIFICATION_CODES_BY_ID")
def test_temp(get_classification_by_code: MagicMock = MagicMock, CLASSIFICATION_CODES_BY_ID: MagicMock = MagicMock) -> None:
    get_classification_by_code().return_value = {
        "8989": {"id": 8989, "name": "Mental Disorders"},
        "8997": {"id": 8997, "name": "Musculoskeletal - Knee", "endDateTime": None},
        "3140": {"id": 3140, "name": "Hearing Loss", "endDateTime": "2036-03-20T00:11:43Z"},
        "8968": {"id": 8968, "name": "digestive", "endDateTime": "2016-03-20T00:11:43Z"},
    }
    # CLASSIFICATION_CODES_BY_ID().return_value = get_classification_by_code
    # with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
    print(get_classification_by_code().return_value)
    print(CLASSIFICATION_CODES_BY_ID)
    print(get_classification(classification_code = 8989))
    print(get_classification(classification_code = 8997))
    print(get_classification(classification_code = 3140))
    print(get_classification(classification_code = 8968))
    
    assert get_classification(9999) is not None
    assert get_classification(9999) is None
