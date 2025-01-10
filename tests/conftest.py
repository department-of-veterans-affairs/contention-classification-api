"""Common test configuration and fixtures."""

import csv
import json
from typing import Any, Dict, Union
from unittest.mock import mock_open, patch

import pytest
from fastapi.testclient import TestClient

from src.python_src.api import app

# Export commonly used imports
__all__ = ["pytest", "json", "csv", "mock_open", "patch", "TestClient"]


# Common test client fixture
@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


# Common mock functions
@pytest.fixture
def mock_file_open() -> Any:
    """Create a mock for file operations."""
    return mock_open


# Common test data
@pytest.fixture
def common_classification_codes() -> Dict[str, Dict[str, Union[int, str]]]:
    """Common classification codes used across tests."""
    return {
        "mental_disorders": {"id": 8989, "name": "Mental Disorders"},
        "knee": {"id": 8997, "name": "Musculoskeletal - Knee"},
        "hearing_loss": {"id": 3140, "name": "Hearing Loss"},
    }


@pytest.fixture
def common_diagnostic_codes() -> Dict[str, Dict[str, Union[int, str]]]:
    """Common diagnostic codes used across tests."""
    return {
        "tuberculosis": {"code": 7710, "name": "Tuberculosis"},
        "respiratory": {"code": 6829, "name": "Respiratory"},
    }


@pytest.fixture
def mock_csv_strings() -> Dict[str, str]:
    """Common CSV strings used across tests."""
    return {
        "diagnostic_csv": (
            "DIAGNOSTIC_CODE,CLASSIFICATION_CODE,CLASSIFICATION_TEXT\n7710,6890,Tuberculosis\n6829,9012,Respiratory\n"
        ),
        "contention_csv": (
            "CONTENTION TEXT,CLASSIFICATION CODE,CLASSIFICATION TEXT\nPTSD,8989,Mental Disorders\nKnee pain,8997,Knee\n"
        ),
        "logging_csv": (
            "Autosuggestion Name,Other Columns\nTinnitus (ringing in ears),data\nPTSD (post-traumatic stress disorder),data\n"
        ),
        "logging_v0_1_csv": (
            "Conditions list terms, organized by base term and variations\n"
            "Base Term,UI Term 1,UI Term 2,UI Term 3,UI Term 4,UI Term 5,UI Term 6\n"
            "tinnitus,Tinnitus,Ringing in ears,,,,\n"
        ),
    }
