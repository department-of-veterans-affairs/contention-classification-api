"""Tests for the BRD classification codes module."""

import json
from typing import Any, Dict, List
from unittest.mock import MagicMock, mock_open, patch
import pytest
from fastapi.testclient import TestClient
import os


from src.python_src.util.classifier_utilities import check_if_classification_expired

mock_data = {
        "items": [
            {"id": 8989, "name": "Mental Disorders"},
            {"id": 8997, "name": "Musculoskeletal - Knee","endDateTime": None},
            {"id": 3140, "name": "Hearing Loss", "endDateTime": "2036-03-20T00:11:43Z"},
            {"id": 8968, "name": "digestive", "endDateTime": "2026-03-20T00:11:43Z"}
        ]
    }

@patch("src.python_src.util.classifier_utilities.get_dict_of_brd")
def test_check_if_classification_enddate_expired(get_dict_of_brd) -> None:
    get_dict_of_brd = MagicMock()
    get_dict_of_brd.return_value = mock_data
    print(f"get_dict_of_brd.return_value: {get_dict_of_brd.return_value}")
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
        result = check_if_classification_expired(classification_code=8968, classification_name="digestive")
        print(result)
        assert result == (None, None)
    
@patch("src.python_src.util.classifier_utilities.get_dict_of_brd")
def test_check_if_classification_enddate_none(get_dict_of_brd) -> None:
    get_dict_of_brd = MagicMock()
    get_dict_of_brd.return_value = mock_data
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
        result = check_if_classification_expired(classification_code=8997, classification_name="Musculoskeletal - Knee")
        print(result)
        assert result == (8997, "Musculoskeletal - Knee")

    
@patch("src.python_src.util.classifier_utilities.get_dict_of_brd")
def test_check_if_classification_enddate_not_expired(get_dict_of_brd) -> None:
    get_dict_of_brd = MagicMock()
    get_dict_of_brd.return_value = mock_data
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
        result = check_if_classification_expired(classification_code=3140, classification_name="Hearing Loss")
        print(result)
        assert result == (3140, "Hearing Loss")
    