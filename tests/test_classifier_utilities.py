from unittest.mock import MagicMock, patch

import httpx

from src.python_src.pydantic_models import (
    AiRequest,
    AiResponse,
    ClassifiedContention,
    ClassifierResponse,
    Contention,
    VaGovClaim,
)
from src.python_src.util.app_utilities import app_config
from src.python_src.util.classifier_utilities import ml_classification, subset_unclassified_contentions, update_classifications

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


def test_subset_unclassified() -> None:
    test_indices, test_ai_request = subset_unclassified_contentions(TEST_RESPONSE, TEST_CLAIM)
    assert test_indices == [1, 2]
    assert isinstance(test_ai_request, AiRequest)
    assert len(test_ai_request.contentions) == 2


def test_subset_unclassified_fully_classified() -> None:
    updated = update_contentions_test(TEST_CONTENTIONS)
    test_response = ClassifierResponse(
        contentions=updated,
        claim_id=1,
        form526_submission_id=1,
        is_fully_classified=True,
        num_processed_contentions=3,
        num_classified_contentions=3,
    )
    result = subset_unclassified_contentions(test_response, TEST_CLAIM)
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


@patch("src.python_src.util.classifier_utilities.AiClient")
@patch("src.python_src.util.classifier_utilities.subset_unclassified_contentions")
@patch("src.python_src.util.classifier_utilities.update_classifications")
def test_ml_classifications_success(mock_update: MagicMock, mock_subset: MagicMock, mock_ai_client: MagicMock) -> None:
    mock_client_instance = mock_ai_client.return_value

    mock_subset.return_value = ([1, 2], AiRequest(contentions=TEST_CLAIM.contentions[1:]))

    mock_client_instance.classify_contention.return_value = AiResponse(
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

    mock_update.return_value = ClassifierResponse(
        contentions=[
            ClassifiedContention(
                classification_code=8998,
                classification_name="Classification Name",
                contention_type="NEW",
            ),
            ClassifiedContention(
                classification_code=9999,
                classification_name="ml classification",
                contention_type="NEW",
            ),
            ClassifiedContention(
                classification_code=9999,
                classification_name="ml classification",
                contention_type="NEW",
            ),
        ],
        claim_id=1,
        form526_submission_id=1,
        is_fully_classified=False,
        num_processed_contentions=3,
        num_classified_contentions=1,
    )

    # Call the ml_classification function
    ml_classification(TEST_RESPONSE, TEST_CLAIM)

    # Assert that the functions are called with the expected arguments
    mock_subset.assert_called_once_with(TEST_RESPONSE, TEST_CLAIM)
    mock_client_instance.classify_contention.assert_called_once_with(
        endpoint=app_config["ai_classification_endpoint"]["endpoint"], data=mock_subset.return_value[1]
    )
    mock_update.assert_called_once_with(
        TEST_RESPONSE, mock_subset.return_value[0], mock_client_instance.classify_contention.return_value
    )


@patch("src.python_src.util.classifier_utilities.log_as_json")
@patch("src.python_src.util.classifier_utilities.update_classifications")
@patch("src.python_src.util.classifier_utilities.subset_unclassified_contentions")
@patch("src.python_src.util.classifier_utilities.AiClient")
def test_ml_classifications_http_error(
    mock_ai_client: MagicMock, mock_subset: MagicMock, mock_update: MagicMock, mock_log: MagicMock
) -> None:
    mock_ai_client_instance = mock_ai_client.return_value

    mock_subset.return_value = ([1, 2], AiRequest(contentions=TEST_CLAIM.contentions[1:]))
    mock_ai_client_instance.classify_contention.side_effect = httpx.HTTPStatusError(
        "Error reaching service", request=MagicMock(), response=MagicMock(status_code=500)
    )
    result = ml_classification(TEST_RESPONSE, TEST_CLAIM)
    mock_ai_client_instance.classify_contention.assert_called_once_with(
        endpoint=app_config["ai_classification_endpoint"]["endpoint"], data=mock_subset.return_value[1]
    )
    mock_update.assert_not_called()
    mock_log.assert_called_once_with({"message": "Failure to reach AI Endpoint", "error": "Error reaching service"})
    assert result == TEST_RESPONSE


@patch("src.python_src.util.classifier_utilities.log_as_json")
@patch("src.python_src.util.classifier_utilities.update_classifications")
@patch("src.python_src.util.classifier_utilities.subset_unclassified_contentions")
@patch("src.python_src.util.classifier_utilities.AiClient")
def test_ml_classifications_request_error(
    mock_ai_client: MagicMock, mock_subset: MagicMock, mock_update: MagicMock, mock_log: MagicMock
) -> None:
    mock_ai_client_instance = mock_ai_client.return_value

    mock_subset.return_value = ([1, 2], AiRequest(contentions=TEST_CLAIM.contentions[1:]))
    mock_ai_client_instance.classify_contention.side_effect = httpx.RequestError("Network error", request=MagicMock())
    result = ml_classification(TEST_RESPONSE, TEST_CLAIM)
    mock_ai_client_instance.classify_contention.assert_called_once_with(
        endpoint=app_config["ai_classification_endpoint"]["endpoint"], data=mock_subset.return_value[1]
    )
    mock_update.assert_not_called()
    mock_log.assert_called_once_with({"message": "Failure to reach AI Endpoint", "error": "Network error"})
    assert result == TEST_RESPONSE
