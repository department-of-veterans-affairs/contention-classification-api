"""Tests for the BRD classification codes module."""

from src.python_src.util.brd_classification_codes import (
    CLASSIFICATION_NAMES_BY_CODE,
    get_classification_name,
    get_classification_names_by_code,
)
from tests.conftest import json, patch, pytest


def test_get_classification_names_by_code(common_classification_codes, mock_file_open):
    """Test get_classification_names_by_code with mock data."""
    mock_data = {
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


def test_get_classification_name(common_classification_codes, mock_file_open):
    """Test get_classification_name with mock data."""
    mock_data = {
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


def test_get_classification_names_by_code_file_error():
    """Test error handling when file cannot be opened."""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        with pytest.raises(FileNotFoundError):
            get_classification_names_by_code()


def test_get_classification_name_file_error():
    """Test error handling when file cannot be opened."""
    with patch.dict(CLASSIFICATION_NAMES_BY_CODE, {}, clear=True):
        result = get_classification_name(8989)
        assert result is None
