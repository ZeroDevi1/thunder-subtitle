from __future__ import annotations

import asyncio
from dataclasses import asdict
from typing import Any, Iterable

import httpx

from .models import ThunderSubtitleResponse, ThunderSubtitleItem


class ThunderAPIError(RuntimeError):
    pass


class ThunderClient:
    def __init__(self, *, base_url: str = "https://api-shoulei-ssl.xunlei.com") -> None:
        self._base_url = base_url.rstrip("/")

    async def search(self, *, query: str, timeout_s: float = 20.0) -> list[ThunderSubtitleItem]:
        if not query:
            return []
        url = f"{self._base_url}/oracle/subtitle"
        async with httpx.AsyncClient(timeout=timeout_s, follow_redirects=True) as client:
            r = await client.get(url, params={"name": query})
            r.raise_for_status()
            data = r.json()
        resp = ThunderSubtitleResponse.from_dict(data)
        if resp.code != 0 or resp.result != "ok":
            return []
        return resp.data

    async def download_bytes(self, *, url: str, timeout_s: float = 60.0) -> bytes:
        async with httpx.AsyncClient(timeout=timeout_s, follow_redirects=True) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.content


async def download_with_retries(
    client: ThunderClient,
    *,
    url: str,
    timeout_s: float,
    retries: int,
    retry_sleep_s: float = 0.5,
) -> bytes:
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return await client.download_bytes(url=url, timeout_s=timeout_s)
        except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as e:
            last_err = e
            if attempt >= retries:
                break
            await asyncio.sleep(retry_sleep_s * (attempt + 1))
    raise ThunderAPIError(f"下载失败（已重试 {retries} 次）：{last_err}") from last_err
