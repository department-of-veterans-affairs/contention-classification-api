"""Tests for the BRD classification codes module."""

from typing import Any, Dict, List, TypedDict, Union

from src.python_src.util.brd_classification_codes import (
    CLASSIFICATION_NAMES_BY_CODE,
    get_classification_name,
    get_classification_names_by_code,
)
from tests.conftest import json, patch, pytest


class ItemDict(TypedDict):
    id: int
    name: str


def test_get_classification_names_by_code(
    common_classification_codes: Dict[str, Dict[str, Union[int, str]]], mock_file_open: Any
) -> None:
    """Test get_classification_names_by_code with mock data."""
    mock_data: Dict[str, List[ItemDict]] = {
        "items": [
            {"id": 8989, "name": "Mental Disorders"},
            {"id": 8997, "name": "Musculoskeletal - Knee"},
            {"id": 3140, "name": "Hearing Loss"},
        ]
    }
    with patch("builtins.open", mock_file_open(read_data=json.dumps(mock_data))):
        result = get_classification_names_by_code()
        assert result == {
            8989: "Mental Disorders",
            8997: "Musculoskeletal - Knee",
            3140: "Hearing Loss",
        }


def test_get_classification_names_by_code_missing_items(mock_file_open: Any) -> None:
    """Test handling when JSON doesn't have 'items' key."""
    mock_data: Dict[str, List[Any]] = {"wrong_key": []}
    with patch("builtins.open", mock_file_open(read_data=json.dumps(mock_data))):
        with pytest.raises(KeyError):
            get_classification_names_by_code()


def test_get_classification_names_by_code_invalid_json(mock_file_open: Any) -> None:
    """Test handling of invalid JSON data."""
    with patch("builtins.open", mock_file_open(read_data="invalid json")):
        with pytest.raises(json.JSONDecodeError):
            get_classification_names_by_code()


def test_get_classification_name(
    common_classification_codes: Dict[str, Dict[str, Union[int, str]]], mock_file_open: Any
) -> None:
    """Test get_classification_name with mock data."""
    mock_data: Dict[str, List[ItemDict]] = {
        "items": [
            {"id": 8989, "name": "Mental Disorders"},
            {"id": 8997, "name": "Musculoskeletal - Knee"},
            {"id": 3140, "name": "Hearing Loss"},
        ]
    }
    with patch("builtins.open", mock_file_open(read_data=json.dumps(mock_data))):
        assert get_classification_name(8989) == "Mental Disorders"
        assert get_classification_name(8997) == "Musculoskeletal - Knee"
        assert get_classification_name(3140) == "Hearing Loss"
        assert get_classification_name(9999) is None


def test_get_classification_names_by_code_file_error() -> None:
    """Test error handling when file cannot be opened."""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        with pytest.raises(FileNotFoundError):
            get_classification_names_by_code()


def test_get_classification_name_file_error() -> None:
    """Test error handling when file cannot be opened."""
    with patch.dict(CLASSIFICATION_NAMES_BY_CODE, {}, clear=True):
        result = get_classification_name(8989)
        assert result is None
