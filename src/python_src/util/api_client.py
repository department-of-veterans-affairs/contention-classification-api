import httpx

from ..pydantic_models import AiRequest, AiResponse


class AiClient:
    def __init__(self, base_url: str) -> None:
        self.client: httpx.Client = httpx.Client(base_url=base_url)

    def classify_contention(self, endpoint: str, data: AiRequest) -> AiResponse:
        response: httpx.Response = self.client.post(endpoint, json=data.model_dump())
        response.raise_for_status()
        return AiResponse(**response.json())

    def close(self) -> None:
        self.client.close()
