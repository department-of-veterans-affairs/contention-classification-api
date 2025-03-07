from unittest.mock import patch

import httpx

from src.python_src.pydantic_models import AiRequest, AiResponse, ClassifiedContention, Contention


@patch("src.python_src.util.api_client.AiClient")
def test_classify_contention(mock_ai_client: httpx.Client) -> None:
    mock_instance = mock_ai_client.return_value
    mock_response = AiResponse(
        classified_contentions=[
            ClassifiedContention(classification_code=9999, classification_name="Ml Classification", contention_type="NEW")
        ]
    )
    mock_instance.classify_contention.return_value = mock_response
    response = mock_instance.classify_contention(
        "http://localhost:8000/classify",
        AiRequest(contentions=[Contention(contention_text="test contention", contention_type="NEW")]),
    )
    assert isinstance(response, AiResponse)
    mock_instance.classify_contention.assert_called_once_with(
        "http://localhost:8000/classify",
        AiRequest(contentions=[Contention(contention_text="test contention", contention_type="NEW")]),
    )
