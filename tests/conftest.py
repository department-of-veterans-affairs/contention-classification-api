"""Common test configuration and fixtures."""

import csv
import json
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
def mock_file_open():
    """Create a mock for file operations."""
    return mock_open


# Common test data
@pytest.fixture
def common_classification_codes():
    """Common classification codes used across tests."""
    return {
        "mental_disorders": {"id": 8989, "name": "Mental Disorders"},
        "knee": {"id": 8997, "name": "Musculoskeletal - Knee"},
        "hearing_loss": {"id": 3140, "name": "Hearing Loss"},
    }


@pytest.fixture
def common_diagnostic_codes():
    """Common diagnostic codes used across tests."""
    return {
        "tuberculosis": {"code": 7710, "name": "Tuberculosis"},
        "respiratory": {"code": 6829, "name": "Respiratory"},
    }
