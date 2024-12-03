"""
Tests for the logging functions in the API. This mocks the log_as_json function and tests that the logging is called
with the correct dict for different situations.  The primary purpose is to test logging contention text to ensure that
there is no PII in the logs.
"""

from unittest.mock import patch

from fastapi import Request
from src.python_src.api import log_claim_stats_v2, log_contention_stats
from src.python_src.pydantic_models import (
    ClassifiedContention,
    ClassifierResponse,
    Contention,
    VaGovClaim,
)
from starlette.datastructures import Headers

test_expanded_request = Request(
    scope={
        "type": "http",
        "method": "POST",
        "path": "/expanded-contention-classification",
        "headers": Headers(),
    }
)

test_current_classifier_request = Request(
    scope={
        "type": "http",
        "method": "POST",
        "path": "/va-gov-claim-classifier",
        "headers": Headers(),
    }
)


@patch("src.python_src.api.log_as_json")
def test_log_contention_stats_expanded(mocked_func):
    """
    Tests the logging of a contention that is classified but considered free text
    """
    test_contention = Contention(
        contention_text="acl tear right",
        contention_type="NEW",
    )
    test_claim = VaGovClaim(
        claim_id=100, form526_submission_id=500, contentions=[test_contention]
    )
    classified_contention = ClassifiedContention(
        classification_code=8997,
        classification_name="Musculoskeletal - Knee",
        diagnostic_code=None,
        contention_type="NEW",
    )
    log_contention_stats(
        test_contention, classified_contention, test_claim, test_expanded_request
    )

    expected_logging_dict = {
        "vagov_claim_id": test_claim.claim_id,
        "claim_type": "new",
        "classification_code": classified_contention.classification_code,
        "classification_name": classified_contention.classification_name,
        "contention_text": "unmapped contention text ['acl tear']",
        "diagnostic_code": "None",
        "is_in_dropdown": False,
        "is_lookup_table_match": True,
        "is_multi_contention": False,
        "endpoint": "/expanded-contention-classification",
        "is_ab_test_claim": False,
        "processed_contention_text": "acl tear",
    }

    mocked_func.assert_called_once_with(expected_logging_dict)


@patch("src.python_src.api.log_as_json")
def test_non_classified_contentions(mocked_func):
    """
    Tests the logging of a contention that is not classified
    """
    test_contention = Contention(
        contention_text="John has an acl tear right",
        contention_type="NEW",
    )
    test_claim = VaGovClaim(
        claim_id=100, form526_submission_id=500, contentions=[test_contention]
    )
    classified_contention = ClassifiedContention(
        classification_code=None,
        classification_name=None,
        diagnostic_code=None,
        contention_type="NEW",
    )
    log_contention_stats(
        test_contention, classified_contention, test_claim, test_expanded_request
    )

    expected_log = {
        "vagov_claim_id": test_claim.claim_id,
        "claim_type": "new",
        "classification_code": classified_contention.classification_code,
        "classification_name": classified_contention.classification_name,
        "contention_text": "unmapped contention text",
        "diagnostic_code": "None",
        "is_in_dropdown": False,
        "is_lookup_table_match": False,
        "is_multi_contention": False,
        "endpoint": "/expanded-contention-classification",
        "is_ab_test_claim": False,
        "processed_contention_text": None,
    }
    mocked_func.assert_called_once_with(expected_log)


@patch("src.python_src.api.log_as_json")
def test_multiple_contentions(mocked_func):
    """
    Tests multiple contentions one from autosuggestion and one that would be considered free text
    """
    test_contentions = [
        Contention(
            contention_text="tinnitus (ringing or hissing in ears)",
            contention_type="NEW",
        ),
        Contention(
            contention_text="anxiety condition due to somethiing that happened",
            contention_type="NEW",
        ),
    ]
    test_claim = VaGovClaim(
        claim_id=100, form526_submission_id=500, contentions=test_contentions
    )
    classified_contentions = [
        ClassifiedContention(
            classification_code=3140,
            classification_name="Hearing Loss",
            diagnostic_code=None,
            contention_type="NEW",
        ),
        ClassifiedContention(
            classification_code=8989,
            classification_name="Mental Disorders",
            diagnostic_code=None,
            contention_type="NEW",
        ),
    ]

    expected_logs = [
        {
            "vagov_claim_id": test_claim.claim_id,
            "claim_type": "new",
            "classification_code": classified_contentions[0].classification_code,
            "classification_name": classified_contentions[0].classification_name,
            "contention_text": "tinnitus (ringing or hissing in ears)",
            "diagnostic_code": "None",
            "is_in_dropdown": True,
            "is_lookup_table_match": True,
            "is_multi_contention": True,
            "endpoint": "/expanded-contention-classification",
            "is_ab_test_claim": False,
            "processed_contention_text": "tinnitus ringing hissing ears",
        },
        {
            "vagov_claim_id": test_claim.claim_id,
            "claim_type": "new",
            "classification_code": classified_contentions[1].classification_code,
            "classification_name": classified_contentions[1].classification_name,
            "contention_text": "unmapped contention text ['anxiety']",
            "diagnostic_code": "None",
            "is_in_dropdown": False,
            "is_lookup_table_match": True,
            "is_multi_contention": True,
            "endpoint": "/expanded-contention-classification",
            "is_ab_test_claim": False,
            "processed_contention_text": "anxiety",
        },
    ]

    for i in range(len(test_contentions)):
        log_contention_stats(
            test_contentions[i],
            classified_contentions[i],
            test_claim,
            test_expanded_request,
        )
        mocked_func.assert_called_with(expected_logs[i])

    assert mocked_func.call_count == 2


@patch("src.python_src.api.log_as_json")
def test_contentions_with_pii(mocked_func):
    """
    Tests that the logging will not log unless completely classified and no PII slips through
    """
    test_contentions = [
        Contention(
            contention_text="dependent claim for child, 111-11-1111",
            contention_type="NEW",
        ),
        Contention(
            contention_text="John Doe(111-11-1111), right acl tear",
            contention_type="NEW",
        ),
    ]
    test_claim = VaGovClaim(
        claim_id=100, form526_submission_id=500, contentions=test_contentions
    )
    classified_contentions = [
        ClassifiedContention(
            classification_code=None,
            classification_name=None,
            diagnostic_code=None,
            contention_type="NEW",
        ),
        ClassifiedContention(
            classification_code=None,
            classification_name="None",
            diagnostic_code=None,
            contention_type="NEW",
        ),
    ]
    expected_logs = [
        {
            "vagov_claim_id": test_claim.claim_id,
            "claim_type": "new",
            "classification_code": classified_contentions[0].classification_code,
            "classification_name": classified_contentions[0].classification_name,
            "contention_text": "unmapped contention text",
            "diagnostic_code": "None",
            "is_in_dropdown": False,
            "is_lookup_table_match": False,
            "is_multi_contention": True,
            "endpoint": "/expanded-contention-classification",
            "is_ab_test_claim": False,
            "processed_contention_text": None,
        },
        {
            "vagov_claim_id": test_claim.claim_id,
            "claim_type": "new",
            "classification_code": classified_contentions[1].classification_code,
            "classification_name": classified_contentions[1].classification_name,
            "contention_text": "unmapped contention text",
            "diagnostic_code": "None",
            "is_in_dropdown": False,
            "is_lookup_table_match": False,
            "is_multi_contention": True,
            "endpoint": "/expanded-contention-classification",
            "is_ab_test_claim": False,
            "processed_contention_text": None,
        },
    ]

    for i in range(len(test_contentions)):
        log_contention_stats(
            test_contentions[i],
            classified_contentions[i],
            test_claim,
            test_expanded_request,
        )
        mocked_func.assert_called_with(expected_logs[i])

    assert mocked_func.call_count == 2


@patch("src.python_src.api.log_as_json")
def test_log_claim_stats(mocked_func):
    test_claim = VaGovClaim(
        claim_id=100,
        form526_submission_id=500,
        contentions=[
            Contention(
                contention_text="acl tear right",
                contention_type="NEW",
            ),
            Contention(
                contention_text="dependent claim, john doe 222-22-2222",
                contention_type="NEW",
            ),
        ],
    )
    classifier_response = ClassifierResponse(
        contentions=[
            ClassifiedContention(
                classification_code=8997,
                classification_name="Muscloskeletal - Knee",
                diagnostic_code=None,
                contention_type="NEW",
            ),
            ClassifiedContention(
                classification_code=None,
                classification_name=None,
                diagnostic_code=None,
                contention_type="NEW",
            ),
        ],
        claim_id=test_claim.claim_id,
        form526_submission_id=test_claim.form526_submission_id,
        is_fully_classified=False,
        num_processed_contentions=2,
        num_classified_contentions=1,
    )

    expected_log = {
        "claim_id": 100,
        "form526_submission_id": 500,
        "is_fully_classified": False,
        "percent_clasified": 50.0,
        "num_processed_contentions": 2,
        "num_classified_contentions": 1,
        "endpoint": "/expanded-contention-classification",
        "is_ab_test_claim": False,
    }
    log_claim_stats_v2(test_claim, classifier_response, test_expanded_request)
    mocked_func.assert_called_once_with(expected_log)


@patch("src.python_src.api.log_as_json")
def test_current_classifier_contention(mocked_func):
    """
    Tests the logging of the current contention logs
    """
    test_contention = Contention(
        contention_text="acl tear right",
        contention_type="NEW",
    )
    test_claim = VaGovClaim(
        claim_id=100, form526_submission_id=500, contentions=[test_contention]
    )
    classified_contention = ClassifiedContention(
        classification_code=None,
        classification_name=None,
        diagnostic_code=None,
        contention_type="NEW",
    )
    log_contention_stats(
        test_contention,
        classified_contention,
        test_claim,
        test_current_classifier_request,
    )

    expected_logging_dict = {
        "vagov_claim_id": test_claim.claim_id,
        "claim_type": "new",
        "classification_code": classified_contention.classification_code,
        "classification_name": classified_contention.classification_name,
        "contention_text": "unmapped contention text",
        "diagnostic_code": "None",
        "is_in_dropdown": False,
        "is_lookup_table_match": False,
        "is_multi_contention": False,
        "endpoint": "/va-gov-claim-classifier",
        "is_ab_test_claim": False,
    }

    mocked_func.assert_called_once_with(expected_logging_dict)


@patch("src.python_src.api.log_as_json")
def test_full_logging_expanded_endpoint(mocked_func):
    """
    Tests full logging including individual contentions and one claim
    """
    test_contentions = [
        Contention(
            contention_text="john doe 111-11-1111 acl tear right",
            contention_type="NEW",
        ),
        Contention(
            contention_text="anxiety condition due to somethiing that happened",
            contention_type="NEW",
        ),
    ]
    test_claim = VaGovClaim(
        claim_id=100, form526_submission_id=500, contentions=test_contentions
    )
    classified_contentions = [
        ClassifiedContention(
            classification_code=None,
            classification_name=None,
            diagnostic_code=None,
            contention_type="NEW",
        ),
        ClassifiedContention(
            classification_code=8989,
            classification_name="Mental Disorders",
            diagnostic_code=None,
            contention_type="NEW",
        ),
    ]

    expected_contention_logs = [
        {
            "vagov_claim_id": test_claim.claim_id,
            "claim_type": "new",
            "classification_code": classified_contentions[0].classification_code,
            "classification_name": classified_contentions[0].classification_name,
            "contention_text": "unmapped contention text",
            "diagnostic_code": "None",
            "is_in_dropdown": False,
            "is_lookup_table_match": False,
            "is_multi_contention": True,
            "endpoint": "/expanded-contention-classification",
            "is_ab_test_claim": False,
            "processed_contention_text": None,
        },
        {
            "vagov_claim_id": test_claim.claim_id,
            "claim_type": "new",
            "classification_code": classified_contentions[1].classification_code,
            "classification_name": classified_contentions[1].classification_name,
            "contention_text": "unmapped contention text ['anxiety']",
            "diagnostic_code": "None",
            "is_in_dropdown": False,
            "is_lookup_table_match": True,
            "is_multi_contention": True,
            "endpoint": "/expanded-contention-classification",
            "is_ab_test_claim": False,
            "processed_contention_text": "anxiety",
        },
    ]

    classifier_response = ClassifierResponse(
        contentions=classified_contentions,
        claim_id=test_claim.claim_id,
        form526_submission_id=test_claim.form526_submission_id,
        is_fully_classified=False,
        num_processed_contentions=2,
        num_classified_contentions=1,
    )
    expected_claim_log = {
        "claim_id": 100,
        "form526_submission_id": 500,
        "is_fully_classified": False,
        "percent_clasified": 50.0,
        "num_processed_contentions": 2,
        "num_classified_contentions": 1,
        "endpoint": "/expanded-contention-classification",
        "is_ab_test_claim": False,
    }

    for i in range(len(test_contentions)):
        log_contention_stats(
            test_contentions[i],
            classified_contentions[i],
            test_claim,
            test_expanded_request,
        )
        mocked_func.assert_called_with(expected_contention_logs[i])

    log_claim_stats_v2(test_claim, classifier_response, test_expanded_request)
    mocked_func.assert_called_with(expected_claim_log)
    assert mocked_func.call_count == 3


@patch("src.python_src.api.log_as_json")
def test_claim_testing_log(mocked_func):
    """
    Tests that the testing claim flag is logged correctly
    """
    test_contention = Contention(
        contention_text="acl tear right",
        contention_type="NEW",
    )
    test_claim = VaGovClaim(
        claim_id=100,
        form526_submission_id=500,
        contentions=[test_contention],
        is_ab_test_claim=True,
    )
    classified_contention = ClassifiedContention(
        classification_code=8997,
        classification_name="Musculoskeletal - Knee",
        diagnostic_code=None,
        contention_type="NEW",
    )
    log_contention_stats(
        test_contention, classified_contention, test_claim, test_expanded_request
    )

    test_response = ClassifierResponse(
        contentions=[classified_contention],
        claim_id=test_claim.claim_id,
        form526_submission_id=test_claim.form526_submission_id,
        is_fully_classified=False,
        num_processed_contentions=1,
        num_classified_contentions=1,
    )

    expected_logging_dict = {
        "vagov_claim_id": test_claim.claim_id,
        "claim_type": "new",
        "classification_code": classified_contention.classification_code,
        "classification_name": classified_contention.classification_name,
        "contention_text": "unmapped contention text ['acl tear']",
        "diagnostic_code": "None",
        "is_in_dropdown": False,
        "is_lookup_table_match": True,
        "is_multi_contention": False,
        "endpoint": "/expanded-contention-classification",
        "is_ab_test_claim": True,
        "processed_contention_text": "acl tear",
    }

    mocked_func.assert_called_with(expected_logging_dict)

    log_claim_stats_v2(test_claim, test_response, test_expanded_request)

    expected_claim_logging_dict = {
        "claim_id": test_claim.claim_id,
        "form526_submission_id": test_claim.form526_submission_id,
        "is_fully_classified": test_response.is_fully_classified,
        "percent_clasified": (
            test_response.num_classified_contentions
            / test_response.num_processed_contentions
        )
        * 100,
        "num_processed_contentions": test_response.num_processed_contentions,
        "num_classified_contentions": test_response.num_classified_contentions,
        "endpoint": "/expanded-contention-classification",
        "is_ab_test_claim": True,
    }

    mocked_func.assert_called_with(expected_claim_logging_dict)
    assert mocked_func.call_count == 2
