"""Tests for the claim linker module."""

import logging
from typing import Generator

from fastapi.testclient import TestClient
from _pytest.logging import LogCaptureFixture


def test_claim_ids_logged(test_client: TestClient, caplog: LogCaptureFixture) -> None:
    json_post_dict = {
        "va_gov_claim_id": 100,
        "vbms_claim_id": 200,
    }
    with caplog.at_level(logging.INFO):
        response = test_client.post("/claim-linker", json=json_post_dict)
        assert response.status_code == 200
        assert response.json() == {"success": True}
        assert "linking claims" in caplog.text
        assert "100" in caplog.text
        assert "200" in caplog.text
