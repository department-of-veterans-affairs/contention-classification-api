# type: ignore
from typing import Dict

import httpx

# from ..pydantic_models import ClassifiedContention, Contention


class AiClient:
    def __init__(self, base_url: str) -> None:
        self.client = httpx.Client(base_url=base_url)

    def classify_contention(self, endpoint: str, data: Dict):
        response = self.client.post(endpoint, json=data)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self.client.close()
