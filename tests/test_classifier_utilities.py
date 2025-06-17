from unittest.mock import MagicMock, call, patch

from src.python_src.pydantic_models import (
    AiRequest,
    AiResponse,
    ClassifiedContention,
    ClassifierResponse,
    Contention,
    VaGovClaim,
)
from src.python_src.util.classifier_utilities import build_ai_request, ml_classify_claim, update_classifications

TEST_CLAIM = VaGovClaim(
    claim_id=100,
    form526_submission_id=500,
    contentions=[
        Contention(contention_text="lower back", contention_type="NEW", diagnostic_code="1234"),
        Contention(
            contention_text="Free Text Entry",
            contention_type="NEW",
        ),
        Contention(contention_text="Not classifiable by CC team", contention_type="claim_for_increase", diagnostic_code=5678),
    ],
)

TEST_CONTENTIONS = [
    ClassifiedContention(
        classification_code=8998,
        classification_name="Classification Name",
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
    contentions=TEST_CONTENTIONS,
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
    updated = update_contentions_test(TEST_CONTENTIONS)
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
    expected = update_classifications(TEST_RESPONSE, test_indices, test_ai_response)
    for idx in test_indices:
        assert expected.contentions[idx].classification_code == 9999
        assert expected.contentions[idx].classification_name == "ml classification"

    assert expected.contentions[0].classification_code == 8998


@patch("src.python_src.util.classifier_utilities.get_classification_code")
@patch("src.python_src.util.classifier_utilities.ml_classifier")
def test_ml_classify_claim(mock_ml_classifier: MagicMock, mock_get_classification_code: MagicMock) -> None:
    mock_ml_classifier.make_predictions.return_value = ["musculoskeletal", "Eye (Vision)"]
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
def test_ml_classify_claim_returns_empty_list_if_no_ml_model() -> None:
    ai_response = ml_classify_claim(TEST_AI_REQUEST)
    assert ai_response.classified_contentions == []
