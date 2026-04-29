from __future__ import annotations

from pathlib import Path

import httpx


class RequestUtils:
    _client: httpx.AsyncClient | None = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None:
            cls._client = httpx.AsyncClient(timeout=60, follow_redirects=True)
        return cls._client

    @classmethod
    async def close(cls) -> None:
        if cls._client is not None:
            await cls._client.aclose()
            cls._client = None

    @classmethod
    async def get(cls, url: str, **kwargs) -> httpx.Response:
        return await cls.get_client().get(url, **kwargs)

    @classmethod
    async def post(cls, url: str, **kwargs) -> httpx.Response:
        return await cls.get_client().post(url, **kwargs)

    @classmethod
    async def request(cls, method: str, url: str, **kwargs) -> httpx.Response:
        return await cls.get_client().request(method, url, **kwargs)

    @classmethod
    async def download(cls, url: str, target: Path) -> None:
        async with cls.get_client().stream("GET", url) as response:
            response.raise_for_status()
            with target.open("wb") as file:
                async for chunk in response.aiter_bytes():
                    file.write(chunk)

