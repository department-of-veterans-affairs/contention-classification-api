from unittest.mock import MagicMock, call, patch

from fastapi import Request
from starlette.datastructures import Headers

from src.python_src.pydantic_models import (
    AiRequest,
    AiResponse,
    ClassifiedContention,
    ClassifierResponse,
    Contention,
    VaGovClaim,
)
from src.python_src.util.classifier_utilities import (
    build_ai_request,
    classify_contention,
    ml_classify_claim,
    supplement_with_ml_classification,
    update_classifications,
)

TEST_CLAIM = VaGovClaim(
    claim_id=100,
    form526_submission_id=500,
    contentions=[
        Contention(contention_text="lower back", contention_type="NEW"),
        Contention(
            contention_text="Free Text Entry",
            contention_type="NEW",
        ),
        Contention(contention_text="Not classifiable by CC team", contention_type="claim_for_increase", diagnostic_code=5678),
    ],
)

TEST_CONTENTION = Contention(contention_text="PTSD", contention_type="NEW", diagnostic_code=None)

TEST_CLASSIFIED_CONTENTIONS = [
    ClassifiedContention(
        classification_code=1215,
        classification_name="shoulder pain",
        contention_type="New",
    ),
    ClassifiedContention(
        classification_code=None,
        classification_name=None,
        diagnostic_code=2,
        contention_type="New",
    ),
    ClassifiedContention(
        classification_code=None,
        classification_name=None,
        diagnostic_code=1250,
        contention_type="claim_for_increase",
    ),
]

TEST_RESPONSE = ClassifierResponse(
    contentions=TEST_CLASSIFIED_CONTENTIONS,
    claim_id=1,
    form526_submission_id=1,
    is_fully_classified=False,
    num_processed_contentions=3,
    num_classified_contentions=0,
)

TEST_AI_REQUEST = AiRequest(
    contentions=[
        Contention(contention_text="lower back", contention_type="NEW", diagnostic_code=1234),
        Contention(contention_text="blurry vision", contention_type="claim_for_increase", diagnostic_code=5678),
    ],
)

TEST_EXPANDED_CLASSIFIER_REQUEST = Request(
    scope={
        "type": "http",
        "method": "POST",
        "path": "/expanded-contention-classification",
        "headers": Headers(),
    }
)

TEST_HYBRID_CLASSIFIER_REQUEST = Request(
    scope={
        "type": "http",
        "method": "POST",
        "path": "/hybrid-contention-classification",
        "headers": Headers(),
    }
)


@patch("src.python_src.util.logging_utilities.log_as_json")
def test_classify_contention_logs_stats(mock_log: MagicMock) -> None:
    classify_contention(TEST_CONTENTION, TEST_CLAIM, TEST_EXPANDED_CLASSIFIER_REQUEST)

    expected_log = {
        "vagov_claim_id": TEST_CLAIM.claim_id,
        "claim_type": "new",
        "classification_code": 8989,
        "classification_name": "Mental Disorders",
        "contention_text": "PTSD",
        "diagnostic_code": "None",
        "is_in_dropdown": False,
        "is_lookup_table_match": True,
        "is_multi_contention": True,
        "endpoint": TEST_EXPANDED_CLASSIFIER_REQUEST.url.path,
        "classification_method": "contention_text",
        "processed_contention_text": "ptsd",
    }

    mock_log.assert_called_once_with(expected_log)


def update_contentions_test(contentions: list[ClassifiedContention]) -> list[ClassifiedContention]:
    updated_contentions = []
    for c in contentions:
        if c.classification_code is None:
            updated_contention = ClassifiedContention(
                classification_code=9999,
                classification_name="Updated Classification",
                diagnostic_code=c.diagnostic_code,
                contention_type=c.contention_type,
            )
            updated_contentions.append(updated_contention)
        else:
            updated_contentions.append(c)
    return updated_contentions


def test_build_request_unclassified() -> None:
    test_indices, test_ai_request = build_ai_request(TEST_RESPONSE, TEST_CLAIM)
    assert test_indices == [1, 2]
    assert isinstance(test_ai_request, AiRequest)
    assert len(test_ai_request.contentions) == 2


def test_build_fully_classified() -> None:
    updated = update_contentions_test(TEST_CLASSIFIED_CONTENTIONS)
    test_response = ClassifierResponse(
        contentions=updated,
        claim_id=1,
        form526_submission_id=1,
        is_fully_classified=True,
        num_processed_contentions=3,
        num_classified_contentions=3,
    )
    result = build_ai_request(test_response, TEST_CLAIM)
    assert result[0] == []
    assert isinstance(result[1], AiRequest)
    assert len(result[1].contentions) == 0


def test_update_classifications() -> None:
    test_ai_response = AiResponse(
        classified_contentions=[
            ClassifiedContention(
                classification_code=9999,
                classification_name="ml classification",
                diagnostic_code=5678,
                contention_type="claim_for_increase",
            ),
            ClassifiedContention(
                classification_code=9999,
                classification_name="ml classification",
                diagnostic_code=2,
                contention_type="NEW",
            ),
        ]
    )
    test_indices = [1, 2]

    expected = update_classifications(TEST_RESPONSE, test_indices, test_ai_response, TEST_HYBRID_CLASSIFIER_REQUEST)
    for idx in test_indices:
        assert expected.contentions[idx].classification_code == 9999
        assert expected.contentions[idx].classification_name == "ml classification"

    assert expected.contentions[0].classification_code == 1215


@patch("src.python_src.util.logging_utilities.ml_classifier")
@patch("src.python_src.util.logging_utilities.log_as_json")
def test_update_classifications_logs_stats(mock_log: MagicMock, mock_ml_classifier: MagicMock) -> None:
    mock_ml_classifier.get_version.return_value = "v001"

    test_ai_response = AiResponse(
        classified_contentions=[
            ClassifiedContention(
                classification_code=2462,
                classification_name="lorem ipsum",
                diagnostic_code=5678,
                contention_type="claim_for_increase",
            )
        ]
    )

    update_classifications(
        TEST_RESPONSE,
        [
            1,
        ],
        test_ai_response,
        TEST_HYBRID_CLASSIFIER_REQUEST,
    )

    expected_log = {
        "vagov_claim_id": TEST_RESPONSE.claim_id,
        "claim_type": "claim_for_increase",
        "classification_code": 2462,
        "classification_name": "lorem ipsum",
        "contention_text": "unmapped contention text",
        "diagnostic_code": 5678,
        "is_in_dropdown": False,
        "is_lookup_table_match": False,
        "is_multi_contention": True,
        "endpoint": TEST_HYBRID_CLASSIFIER_REQUEST.url.path,
        "classification_method": "ml_classifier",
        "ml_classifier_version": "v001",
    }

    mock_log.assert_called_once_with(expected_log)


@patch("src.python_src.util.classifier_utilities.log_as_json")
def test_update_classifications_logs_mismatch(mocked_func: MagicMock) -> None:
    """
    Tests that a log message is generated if there is a mismatch
    between how many contentions were expected to be updated versus
    how many were returned in the AiResponse
    """
    test_ai_response = AiResponse(
        classified_contentions=[
            ClassifiedContention(
                classification_code=9999,
                classification_name="ml classification",
                diagnostic_code=5678,
                contention_type="claim_for_increase",
            ),
        ]
    )
    update_classifications(
        TEST_RESPONSE,
        [
            1,
            2,
        ],
        test_ai_response,
        TEST_HYBRID_CLASSIFIER_REQUEST,
    )
    mocked_func.assert_called_once_with({"message": "Mismatched contentions between AiResponse and original classifications"})


@patch("src.python_src.util.classifier_utilities.get_classification_code")
@patch("src.python_src.util.classifier_utilities.ml_classifier")
def test_ml_classify_claim(mock_ml_classifier: MagicMock, mock_get_classification_code: MagicMock) -> None:
    mock_ml_classifier.make_predictions.return_value = [
        ("musculoskeletal", {"musculoskeletal": 0.92, "Eye (Vision)": 0.98}),
        ("Eye (Vision)", {"musculoskeletal": 0.92, "Eye (Vision)": 0.98}),
    ]
    mock_get_classification_code.return_value = "777"

    ai_response = ml_classify_claim(TEST_AI_REQUEST)

    mock_ml_classifier.make_predictions.assert_called_with(["lower back", "blurry vision"])
    mock_get_classification_code.assert_has_calls([call("musculoskeletal"), call("Eye (Vision)")])
    assert ai_response.classified_contentions == [
        ClassifiedContention(
            classification_code="777",
            classification_name="musculoskeletal",
            diagnostic_code="1234",
            contention_type="NEW",
        ),
        ClassifiedContention(
            classification_code="777",
            classification_name="Eye (Vision)",
            diagnostic_code="5678",
            contention_type="claim_for_increase",
        ),
    ]


@patch("src.python_src.util.classifier_utilities.ml_classifier", None)
def test_ml_classify_claim_returns_list_of_no_classification_codes_if_no_ml_model() -> None:
    ai_response = ml_classify_claim(TEST_AI_REQUEST)
    assert len(ai_response.classified_contentions) == len(TEST_AI_REQUEST.contentions)
    assert [c.classification_code for c in ai_response.classified_contentions] == [None] * len(TEST_AI_REQUEST.contentions)


@patch("src.python_src.util.classifier_utilities.build_ai_request")
@patch("src.python_src.util.classifier_utilities.ml_classify_claim")
@patch("src.python_src.util.classifier_utilities.update_classifications")
def test_supplement_with_ml_classifier(
    mock_update_classifications: MagicMock, mock_ml_classify_claim: MagicMock, mock_build_ai_request: MagicMock
) -> None:
    mock_build_ai_request.return_value = [1, 2], TEST_AI_REQUEST
    mock_update_classifications.return_value = TEST_RESPONSE

    supplement_response = supplement_with_ml_classification(TEST_RESPONSE, TEST_CLAIM, TEST_HYBRID_CLASSIFIER_REQUEST)
    assert TEST_RESPONSE == supplement_response

    mock_build_ai_request.assert_called_once()
    mock_ml_classify_claim.assert_called_once()
    mock_update_classifications.assert_called_once()
