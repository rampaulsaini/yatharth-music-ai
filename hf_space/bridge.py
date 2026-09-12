"""Small, testable client for the Yatharth Music AI HTTP API."""

from typing import Any
from urllib.parse import urljoin

import httpx


class YatharthAPIError(RuntimeError):
    """Raised when the Yatharth API cannot complete a request."""


class YatharthBridge:
    def __init__(self, base_url: str, token: str = "", timeout: float = 90) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.token = token.strip()
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def absolute_url(self, path: str) -> str:
        if path.startswith(("http://", "https://")):
            return path
        return urljoin(self.base_url, path.lstrip("/"))

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = httpx.request(
                method,
                self.absolute_url(path),
                headers=self._headers(),
                timeout=self.timeout,
                **kwargs,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise YatharthAPIError(str(exc)) from exc
        if not isinstance(payload, dict):
            raise YatharthAPIError("Yatharth API returned a non-object response")
        return payload

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/api/health")

    def generate(self, **request: Any) -> dict[str, Any]:
        return self._request("POST", "/api/generate", json=request)

    def task(self, task_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/tasks/{task_id}")
