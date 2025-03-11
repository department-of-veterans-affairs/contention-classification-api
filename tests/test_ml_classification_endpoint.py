from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.python_src.pydantic_models import ClassifiedContention, ClassifierResponse, Contention, VaGovClaim


@patch("src.python_src.api.classify_claim")
@patch("src.python_src.api.ml_classification")
def test_hybrid_classifier_fully_classified(
    mock_ml_class: MagicMock, mock_classify_claim: MagicMock, test_client: TestClient
) -> None:
    test_claim = VaGovClaim(
        claim_id=100,
        form526_submission_id=500,
        contentions=[
            Contention(
                contention_text="lower back",
                contention_type="NEW",
            ),
            Contention(contention_text="CFI Contention", contention_type="claim_for_increase", diagnostic_code=5051),
        ],
    )
    mock_classify_claim.return_value = ClassifierResponse(
        contentions=[
            ClassifiedContention(
                classification_code=8998,
                classification_name="Musculoskeletal - Mid/Lower Back (Thoracolumbar Spine)",
                diagnostic_code=None,
                contention_type="NEW",
            ),
            ClassifiedContention(
                classification_code=9002,
                classification_name="Musculoskeletal - Shoulder",
                diagnostic_code=5051,
                contention_type="claim_for_increase",
            ),
        ],
        claim_id=100,
        form526_submission_id=500,
        is_fully_classified=True,
        num_processed_contentions=2,
        num_classified_contentions=2,
    )
    test_client.post("/hybrid-contention-classification", json=test_claim.model_dump())
    mock_classify_claim.assert_called_once()
    mock_ml_class.assert_not_called()


@patch("src.python_src.api.classify_claim")
@patch("src.python_src.api.ml_classification")
def test_hybrid_classifier_partially_classified(
    mock_ml_class: MagicMock, mock_classify_claim: MagicMock, test_client: TestClient
) -> None:
    test_claim = VaGovClaim(
        claim_id=100,
        form526_submission_id=500,
        contentions=[
            Contention(
                contention_text="lower back",
                contention_type="NEW",
            ),
            Contention(contention_text="Unclassifiable", contention_type="NEW"),
        ],
    )
    mock_classify_claim.return_value = ClassifierResponse(
        contentions=[
            ClassifiedContention(
                classification_code=8998,
                classification_name="Musculoskeletal - Mid/Lower Back (Thoracolumbar Spine)",
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
        num_processed_contentions=2,
        num_classified_contentions=1,
    )
    mock_ml_class.return_value = ClassifierResponse(
        contentions=[
            ClassifiedContention(
                classification_code=8998,
                classification_name="Musculoskeletal - Mid/Lower Back (Thoracolumbar Spine)",
                diagnostic_code=None,
                contention_type="NEW",
            ),
            ClassifiedContention(
                classification_code=9999,
                classification_name="ml classification",
                diagnostic_code=5051,
                contention_type="claim_for_increase",
            ),
        ],
        claim_id=100,
        form526_submission_id=500,
        is_fully_classified=False,
        num_processed_contentions=2,
        num_classified_contentions=1,
    )
    test_response = test_client.post("/hybrid-contention-classification", json=test_claim.model_dump())
    mock_classify_claim.assert_called_once()
    mock_ml_class.assert_called_once()
    assert test_response.json()["num_classified_contentions"] == 2
    assert test_response.json()["is_fully_classified"]
