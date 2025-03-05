from typing import Any, Dict, List

import httpx


class AiClient:
    def __init__(self, base_url: str) -> None:
        self.client: httpx.Client = httpx.Client(base_url=base_url)

    def classify_contention(self, endpoint: str, data: List[Dict[str, Any]]) -> Any:
        response: httpx.Response = self.client.post(endpoint, json=data)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self.client.close()
