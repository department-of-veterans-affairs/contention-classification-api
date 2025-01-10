import logging

from _pytest.logging import LogCaptureFixture
from fastapi.testclient import TestClient


def test_claim_ids_logged(client: TestClient, caplog: LogCaptureFixture) -> None:
    json_post_dict = {
        "va_gov_claim_id": 100,
        "vbms_claim_id": 200,
    }

    with caplog.at_level(logging.INFO):
        client.post("/claim-linker", json=json_post_dict)

    expected_claim_link_json = {
        "level": "info",
        "message": "linking claims",
        "va_gov_claim_id": 100,
        "vbms_claim_id": 200,
    }
    log_as_dict = eval(caplog.records[0].message)
    del log_as_dict["date"]
    assert log_as_dict == expected_claim_link_json
