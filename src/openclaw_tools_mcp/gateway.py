"""OpenClaw Gateway client."""

import os
import httpx
from typing import Any


class OpenClawGateway:
    """Client for communicating with OpenClaw Gateway."""

    def __init__(
        self,
        url: str | None = None,
        token: str | None = None,
        timeout: float = 30.0,
    ):
        self.url = url or os.getenv("OPENCLAW_GATEWAY_URL", "http://localhost:18789")
        self.token = token or os.getenv("OPENCLAW_GATEWAY_TOKEN", "")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            self._client = httpx.AsyncClient(
                base_url=self.url,
                headers=headers,
                timeout=self.timeout,
            )
        return self._client

    async def call_tool(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Call an OpenClaw tool via Gateway API.

        Args:
            tool_name: Name of the tool (e.g., "cron", "memory_search")
            params: Tool parameters

        Returns:
            Tool result as dictionary
        """
        client = await self._get_client()

        # Gateway RPC endpoint
        response = await client.post(
            "/rpc",
            json={
                "method": f"tools.{tool_name}",
                "params": params,
            },
        )
        response.raise_for_status()

        data = response.json()
        if "error" in data:
            raise Exception(data["error"])

        return data.get("result", {})

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
