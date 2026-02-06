from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ThunderSubtitleItem:
    gcid: str
    cid: str
    url: str
    ext: str
    name: str
    duration: int
    languages: list[str]
    source: int
    score: float
    fingerprintf_score: float
    extra_name: str
    mt: int

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "ThunderSubtitleItem":
        return ThunderSubtitleItem(
            gcid=str(d.get("gcid", "")),
            cid=str(d.get("cid", "")),
            url=str(d.get("url", "")),
            ext=str(d.get("ext", "")),
            name=str(d.get("name", "")),
            duration=int(d.get("duration", 0) or 0),
            languages=list(d.get("languages") or []),
            source=int(d.get("source", 0) or 0),
            score=float(d.get("score", 0) or 0),
            fingerprintf_score=float(d.get("fingerprintf_score", 0) or 0),
            extra_name=str(d.get("extra_name", "")),
            mt=int(d.get("mt", 0) or 0),
        )


@dataclass(frozen=True, slots=True)
class ThunderSubtitleResponse:
    code: int
    result: str
    data: list[ThunderSubtitleItem]

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "ThunderSubtitleResponse":
        code_raw = d.get("code", -1)
        items = [ThunderSubtitleItem.from_dict(x) for x in (d.get("data") or [])]
        return ThunderSubtitleResponse(
            code=int(code_raw) if code_raw is not None else -1,
            result=str(d.get("result", "")),
            data=items,
        )
