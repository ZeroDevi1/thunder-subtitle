from __future__ import annotations

import asyncio

import respx
import httpx

from thunder_subtitle_cli.client import ThunderClient


@respx.mock
def test_search_parses_ok_response() -> None:
    route = respx.get("https://api-shoulei-ssl.xunlei.com/oracle/subtitle").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": 0,
                "result": "ok",
                "data": [
                    {"gcid": "g1", "cid": "c1", "url": "https://u/1", "ext": "srt", "name": "A", "duration": 1, "languages": ["zh-CN"], "source": 0, "score": 1.2, "fingerprintf_score": 0, "extra_name": "", "mt": 0},
                    {"gcid": "g2", "cid": "c2", "url": "https://u/2", "ext": "ass", "name": "B", "duration": 1, "languages": ["zh-CN"], "source": 0, "score": 9.9, "fingerprintf_score": 0, "extra_name": "x", "mt": 0},
                ],
            },
        )
    )
    client = ThunderClient()
    items = asyncio.run(client.search(query="q", timeout_s=5.0))
    assert route.called
    assert len(items) == 2


@respx.mock
def test_search_returns_empty_on_non_ok_response() -> None:
    respx.get("https://api-shoulei-ssl.xunlei.com/oracle/subtitle").mock(
        return_value=httpx.Response(200, json={"code": 1, "result": "fail", "data": []}),
    )
    client = ThunderClient()
    items = asyncio.run(client.search(query="q", timeout_s=5.0))
    assert items == []
