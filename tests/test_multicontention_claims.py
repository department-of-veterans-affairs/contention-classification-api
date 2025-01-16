"""Tests for the multicontention claims module."""

from fastapi.testclient import TestClient


def test_vagov_classifier_mixed_types(test_client: TestClient) -> None:
    """
    Tests response of multi-contention claims matches expected values
    """
    json_post_dict = {
        "claim_id": 100,
        "form526_submission_id": 500,
        "contentions": [
            {
                "contention_text": "tinnitus (ringing or hissing in ears)",
                "contention_type": "NEW",
            },
            {
                "contention_text": "asthma",
                "contention_type": "INCREASE",
                "diagnostic_code": 8550,
            },
            {
                "contention_text": "free text entry",
                "contention_type": "NEW",
                "diagnostic_code": None,
            },
        ],
    }
    response = test_client.post("/va-gov-claim-classifier", json=json_post_dict)
    assert response.status_code == 200
    assert response.json()["contentions"] == [
        {
            "classification_code": 3140,
            "classification_name": "Hearing Loss",
            "diagnostic_code": None,
            "contention_type": "NEW",
        },
        {
            "classification_code": 9012,
            "classification_name": "Respiratory",
            "diagnostic_code": 8550,
            "contention_type": "INCREASE",
        },
        {
            "classification_code": None,
            "classification_name": None,
            "diagnostic_code": None,
            "contention_type": "NEW",
        },
    ]


def test_vagov_classifier_empty_contentions(test_client: TestClient) -> None:
    """
    Tests 422 is returned when contentions is empty
    """
    json_post_dict = {
        "claim_id": 100,
        "form526_submission_id": 500,
        "contentions": [],
    }
    response = test_client.post("/va-gov-claim-classifier", json=json_post_dict)
    assert response.status_code == 422


def test_vagov_classifier_missing_params(test_client: TestClient) -> None:
    """
    Tests 422 is returned when contentions is empty
    """
    json_post_dict = {
        "contentions": [
            {
                "contention_text": "tinnitus (ringing or hissing in ears)",
                "contention_type": "NEW",
            },
            {
                "contention_text": "asthma",
                "contention_type": "INCREASE",
                "diagnostic_code": 8550,
            },
            {
                "contention_text": "free text entry",
                "contention_type": "NEW",
                "diagnostic_code": None,
            },
        ],
    }
    response = test_client.post("/va-gov-claim-classifier", json=json_post_dict)
    assert response.status_code == 422


def test_single_contention(test_client: TestClient) -> None:
    """
    Tests response of single contention claim matches expected values
    """
    json_post_dict = {
        "claim_id": 100,
        "form526_submission_id": 500,
        "contentions": [
            {
                "contention_text": "asthma",
                "contention_type": "NEW",
            },
        ],
    }
    response = test_client.post("/va-gov-claim-classifier", json=json_post_dict)
    assert response.status_code == 200
    assert response.json()["contentions"] == [
        {
            "classification_code": 9012,
            "classification_name": "Respiratory",
            "diagnostic_code": None,
            "contention_type": "NEW",
        }
    ]


def test_order_response(test_client: TestClient) -> None:
    """
    Tests to make sure that the order of the response matches the
    order of input
    """
    json_post_dict = json_post_dict = {
        "claim_id": 100,
        "form526_submission_id": 500,
        "contentions": [
            {
                "contention_text": "tinnitus (ringing or hissing in ears)",
                "contention_type": "NEW",
            },
            {
                "contention_text": "asthma",
                "contention_type": "INCREASE",
                "diagnostic_code": 8550,
            },
            {
                "contention_text": "free text entry",
                "contention_type": "NEW",
                "diagnostic_code": None,
            },
        ],
    }
    response = test_client.post("/va-gov-claim-classifier", json=json_post_dict)
    expected_order = [3140, 9012, None]
    for i in range(len(response.json()["contentions"])):
        assert response.json()["contentions"][i]["classification_code"] == expected_order[i]


def test_case_insensitivity(test_client: TestClient) -> None:
    """
    Tests that the classifier is case insensitive
    """
    json_post_dict = {
        "claim_id": 100,
        "form526_submission_id": 500,
        "contentions": [
            {
                "contention_text": "TINNITUS (ringing or hissing in ears)",
                "contention_type": "NEW",
            },
            {
                "contention_text": "ASTHMA",
                "contention_type": "INCREASE",
                "diagnostic_code": 8550,
            },
            {
                "contention_text": "FREE TEXT ENTRY",
                "contention_type": "NEW",
                "diagnostic_code": None,
            },
        ],
    }
    response = test_client.post("/va-gov-claim-classifier", json=json_post_dict)
    assert response.status_code == 200
    assert response.json()["contentions"] == [
        {
            "classification_code": 3140,
            "classification_name": "Hearing Loss",
            "diagnostic_code": None,
            "contention_type": "NEW",
        },
        {
            "classification_code": 9012,
            "classification_name": "Respiratory",
            "diagnostic_code": 8550,
            "contention_type": "INCREASE",
        },
        {
            "classification_code": None,
            "classification_name": None,
            "diagnostic_code": None,
            "contention_type": "NEW",
        },
    ]


def test_whitespace_removal(test_client: TestClient) -> None:
    json_post_dict = {
        "claim_id": 100,
        "form526_submission_id": 500,
        "contentions": [
            {
                "contention_text": "    tinnitus (ringing or hissing in ears)    ",
                "contention_type": "NEW",
            }
        ],
    }
    response = test_client.post("/va-gov-claim-classifier", json=json_post_dict)
    assert response.status_code == 200
    assert response.json()["contentions"] == [
        {
            "classification_code": 3140,
            "classification_name": "Hearing Loss",
            "diagnostic_code": None,
            "contention_type": "NEW",
        }
    ]


def test_v5_v6_lookup_values(test_client: TestClient) -> None:
    """
    This tests new classification mappings in v5 of the condition dropdown list
    and v6 of the diagnostic code lookup tables.
    """
    json_post_dict = {
        "claim_id": 100,
        "form526_submission_id": 500,
        "contentions": [
            {
                "contention_text": "PTSD (post-traumatic stress disorder)",
                "contention_type": "NEW",
            },
            {
                "contention_text": "",
                "contention_type": "INCREASE",
                "diagnostic_code": 5012,
            },
        ],
    }
    response = test_client.post("/va-gov-claim-classifier", json=json_post_dict)
    expected_classifications = [
        {"classification_code": 8989, "classification_name": "Mental Disorders"},
        {
            "classification_code": 8940,
            "classification_name": "Cancer - Musculoskeletal - Other",
        },
    ]
    returned_classifications = [
        {
            "classification_code": c["classification_code"],
            "classification_name": c["classification_name"],
        }
        for c in response.json()["contentions"]
    ]
    assert expected_classifications == returned_classifications
