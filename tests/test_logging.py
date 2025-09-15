"""
Tests for the logging functions in the API. This mocks the log_as_json function and tests that the logging is called
with the correct dict for different situations.  The primary purpose is to test logging contention text to ensure that
there is no PII in the logs.
"""

import logging
import sys
from importlib import reload
from unittest.mock import Mock, patch

from fastapi import Request
from starlette.datastructures import Headers

from src.python_src.pydantic_models import (
    AiResponse,
    ClassifiedContention,
    ClassifierResponse,
    Contention,
    VaGovClaim,
)
from src.python_src.util.app_utilities import expanded_lookup_table
from src.python_src.util.classifier_utilities import get_classification_code_name
from src.python_src.util.logging_utilities import log_claim_stats_v2, log_contention_stats, log_ml_contention_stats

test_expanded_request = Request(
    scope={
        "type": "http",
        "method": "POST",
        "path": "/expanded-contention-classification",
        "headers": Headers(),
    }
)

test_hybrid_request = Request(
    scope={
        "type": "http",
        "method": "POST",
        "path": "/hybrid-contention-classification",
        "headers": Headers(),
    }
)


@patch("logging.basicConfig")
def test_logging_calls_basicConfig(mock_basicConfig: Mock) -> None:
    from src.python_src.util import logging_utilities

    reload(logging_utilities)
    mock_basicConfig.assert_called_once_with(
        format="%(message)s", level=logging.INFO, datefmt="%Y-%m-%dT%H:%M:%S%z", stream=sys.stdout, force=True
    )


def test_create_classification_method_new() -> None:
    """
    Tests the logic of creating the classification_method field for logging
    """
    test_contention = Contention(
        contention_text="acl tear right",
        contention_type="NEW",
    )
    classification_method_expanded = get_classification_code_name(test_contention, expanded_lookup_table)[2]
    assert classification_method_expanded == "contention_text"


def test_create_classification_method_inc() -> None:
    """
    Tests the logic of creating the classification_method field for logging
    """
    test_contention_dc = Contention(
        contention_text="",
        contention_type="INCREASE",
        diagnostic_code=5012,
    )
    test_contention_lookup = Contention(
        contention_text="hearing loss",
        contention_type="INCREASE",
        diagnostic_code=501,
    )

    classification_method_dc = get_classification_code_name(test_contention_dc, expanded_lookup_table)[2]
    classification_method_lookup = get_classification_code_name(test_contention_lookup, expanded_lookup_table)[2]
    assert classification_method_dc == "diagnostic_code"
    assert classification_method_lookup == "contention_text"


def test_create_classification_method_not_classed() -> None:
    """
    Tests the logic of creating the classification_method field for logging
    """
    test_contention_test = Contention(
        contention_text="free text entry",
        contention_type="NEW",
    )
    classification_method = get_classification_code_name(test_contention_test, expanded_lookup_table)[2]
    assert classification_method == "not classified"


@patch("src.python_src.util.logging_utilities.log_as_json")
def test_log_contention_stats_expanded(mocked_func: Mock) -> None:
    """
    Tests the logging of a contention that is classified but considered free text
    """
    test_contention = Contention(
        contention_text="knee",
        contention_type="NEW",
    )
    test_claim = VaGovClaim(claim_id=100, form526_submission_id=500, contentions=[test_contention])
    classified_contention = ClassifiedContention(
        classification_code=8997,
        classification_name="Musculoskeletal - Knee",
        diagnostic_code=None,
        contention_type="NEW",
    )
    classified_by = "contention text"
    log_contention_stats(
        test_contention,
        classified_contention,
        test_claim,
        test_expanded_request,
        classified_by,
    )

    expected_logging_dict = {
        "vagov_claim_id": test_claim.claim_id,
        "claim_type": "new",
        "classification_code": classified_contention.classification_code,
        "classification_name": classified_contention.classification_name,
        "contention_text": "unmapped contention text ['knee']",
        "diagnostic_code": "None",
        "is_in_dropdown": False,
        "is_lookup_table_match": True,
        "is_multi_contention": False,
        "endpoint": "/expanded-contention-classification",
        "processed_contention_text": "knee",
        "classification_method": "contention text",
    }
    
    mocked_func.assert_called_once_with(expected_logging_dict)


@patch("src.python_src.util.logging_utilities.log_as_json")
@patch("src.python_src.util.logging_utilities.log_expanded_contention_text")
def test_requests_for_hybrid_endpoint_calls_expanded_logging(
    log_expanded_contention_text: Mock, mock_log_as_json: Mock
) -> None:
    hybrid_request = Request(
        scope={
            "type": "http",
            "method": "POST",
            "path": "/hybrid-contention-classification",
            "headers": Headers(),
        }
    )
    test_contention = Contention(
        contention_text="knee",
        contention_type="NEW",
    )
    test_claim = VaGovClaim(claim_id=100, form526_submission_id=500, contentions=[test_contention])
    classified_contention = ClassifiedContention(
        classification_code=8997,
        classification_name="Musculoskeletal - Knee",
        diagnostic_code=None,
        contention_type="NEW",
    )
    classified_by = "not classified"
    log_contention_stats(
        test_contention,
        classified_contention,
        test_claim,
        hybrid_request,
        classified_by,
    )
    log_expanded_contention_text.assert_called_once()


@patch("src.python_src.util.logging_utilities.log_as_json")
def test_non_classified_contentions(mocked_func: Mock) -> None:
    """
    Tests the logging of a contention that is not classified
    """
    test_contention = Contention(
        contention_text="John has an acl tear right",
        contention_type="NEW",
    )
    test_claim = VaGovClaim(claim_id=100, form526_submission_id=500, contentions=[test_contention])
    classified_contention = ClassifiedContention(
        classification_code=None,
        classification_name=None,
        diagnostic_code=None,
        contention_type="NEW",
    )
    classified_by = "not classified"
    log_contention_stats(
        test_contention,
        classified_contention,
        test_claim,
        test_expanded_request,
        classified_by,
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
        "processed_contention_text": None,
        "classification_method": classified_by,
    }
    mocked_func.assert_called_once_with(expected_log)


@patch("src.python_src.util.logging_utilities.log_as_json")
def test_multiple_contentions(mocked_func: Mock) -> None:
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
    test_claim = VaGovClaim(claim_id=100, form526_submission_id=500, contentions=test_contentions)
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
    classified_by = "contention_text"

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
            "processed_contention_text": "tinnitus ringing hissing ears",
            "classification_method": classified_by,
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
            "processed_contention_text": "anxiety",
            "classification_method": classified_by,
        },
    ]

    for i in range(len(test_contentions)):
        log_contention_stats(
            test_contentions[i],
            classified_contentions[i],
            test_claim,
            test_expanded_request,
            classified_by,
        )
        mocked_func.assert_called_with(expected_logs[i])

    assert mocked_func.call_count == 2


@patch("src.python_src.util.logging_utilities.log_as_json")
def test_contentions_with_pii(mocked_func: Mock) -> None:
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
    test_claim = VaGovClaim(claim_id=100, form526_submission_id=500, contentions=test_contentions)
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
    classified_by = "not classified"
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
            "processed_contention_text": None,
            "classification_method": classified_by,
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
            "processed_contention_text": None,
            "classification_method": classified_by,
        },
    ]

    for i in range(len(test_contentions)):
        log_contention_stats(
            test_contentions[i],
            classified_contentions[i],
            test_claim,
            test_expanded_request,
            classified_by,
        )
        mocked_func.assert_called_with(expected_logs[i])

    assert mocked_func.call_count == 2


@patch("src.python_src.util.logging_utilities.log_as_json")
def test_log_claim_stats(mocked_func: Mock) -> None:
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
    }
    log_claim_stats_v2(test_claim, classifier_response, test_expanded_request)
    mocked_func.assert_called_once_with(expected_log)


@patch("src.python_src.util.logging_utilities.log_as_json")
def test_full_logging_expanded_endpoint(mocked_func: Mock) -> None:
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
    test_claim = VaGovClaim(claim_id=100, form526_submission_id=500, contentions=test_contentions)
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
    classified_by = "contention_text"
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
            "classification_method": classified_by,
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
            "processed_contention_text": "anxiety",
            "classification_method": classified_by,
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
    }

    for i in range(len(test_contentions)):
        log_contention_stats(
            test_contentions[i],
            classified_contentions[i],
            test_claim,
            test_expanded_request,
            classified_by,
        )
        mocked_func.assert_called_with(expected_contention_logs[i])

    log_claim_stats_v2(test_claim, classifier_response, test_expanded_request)
    mocked_func.assert_called_with(expected_claim_log)
    assert mocked_func.call_count == 3


@patch("src.python_src.util.logging_utilities.ml_classifier")
@patch("src.python_src.util.logging_utilities.log_as_json")
def test_multi_contention_claim_logging_ml_classifier(mock_log: Mock, mock_ml_classifier: Mock) -> None:
    """
    Tests logging for multi-contention claims processed by the ML classifier
    """
    mock_ml_classifier.get_version.return_value = "v001"

    test_AI_response = AiResponse(
        classified_contentions=[
            ClassifiedContention(
                classification_code=1234,
                classification_name="lorem",
                diagnostic_code=None,
                contention_type="NEW",
            ),
            ClassifiedContention(
                classification_code=5678,
                classification_name="ipsum dolor",
                diagnostic_code=None,
                contention_type="NEW",
            ),
        ]
    )
    response = ClassifierResponse(
        contentions=[
            ClassifiedContention(
                classification_code=8997,
                classification_name="Classification Name",
                contention_type="NEW",
            ),
            ClassifiedContention(
                classification_code=None,
                classification_name=None,
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
        claim_id=100,
        form526_submission_id=500,
        is_fully_classified=False,
        num_processed_contentions=3,
        num_classified_contentions=1,
    )

    log_ml_contention_stats(response, test_AI_response, test_hybrid_request)
    
    expected_logs = [
        {
            "vagov_claim_id": 100,
            "claim_type": "new",
            "classification_code": 1234,
            "classification_name": "lorem",
            "contention_text": "unmapped contention text",
            "diagnostic_code": None,
            "is_in_dropdown": False,
            "is_lookup_table_match": False,
            "is_multi_contention": True, 
            "endpoint": "/hybrid-contention-classification",
            "classification_method": "ml_classifier",
            "ml_classifier_version": "v001",
        },
        {
            "vagov_claim_id": 100,
            "claim_type": "new",
            "classification_code": 5678,
            "classification_name": "ipsum dolor",
            "contention_text": "unmapped contention text",
            "diagnostic_code": None,
            "is_in_dropdown": False,
            "is_lookup_table_match": False,
            "is_multi_contention": True, 
            "endpoint": "/hybrid-contention-classification",
            "classification_method": "ml_classifier",
            "ml_classifier_version": "v001",
        }
    ]
    # Check that the expected payloads were received by the mocked log_as_json
    assert mock_log.call_count == 2
    all_log_calls = mock_log.call_args_list
    for i in range(len(all_log_calls)):
        args, kwargs = all_log_calls[i]
        assert expected_logs[i] == args[0]

@patch("src.python_src.util.logging_utilities.ml_classifier")
@patch("src.python_src.util.logging_utilities.log_as_json")
def test_single_contention_claim_logging_ml_classifier(mock_log: Mock, mock_ml_classifier: Mock) -> None:
    """
    Tests logging for single-contention claims processed by the ML classifier
    """
    mock_ml_classifier.get_version.return_value = "v001"

    test_AI_response = AiResponse(
        classified_contentions=[
            ClassifiedContention(
                classification_code=1357,
                classification_name="lorem ipsum dolor",
                diagnostic_code=None,
                contention_type="NEW",
            )
        ]
    )

    response = ClassifierResponse(
        contentions=[
            ClassifiedContention(
                classification_code=None,
                classification_name=None,
                diagnostic_code=None,
                contention_type="NEW",
            )
        ],
        claim_id=200,
        form526_submission_id=700,
        is_fully_classified=False,
        num_processed_contentions=1,
        num_classified_contentions=0,
    )

    log_ml_contention_stats(response, test_AI_response, test_hybrid_request)
    
    expected_log = {
            "vagov_claim_id": 200,
            "claim_type": "new",
            "classification_code": 1357,
            "classification_name": "lorem ipsum dolor",
            "contention_text": "unmapped contention text",
            "diagnostic_code": None,
            "is_in_dropdown": False,
            "is_lookup_table_match": False,
            "is_multi_contention": False, 
            "endpoint": "/hybrid-contention-classification",
            "classification_method": "ml_classifier",
            "ml_classifier_version": "v001",
        }

    # Check that the expected payload was received by the mocked log_as_json
    assert mock_log.call_count == 1
    assert mock_log.call_args[0][0] == expected_log
