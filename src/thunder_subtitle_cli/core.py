from __future__ import annotations

import asyncio
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from .client import ThunderClient, download_with_retries
from .models import ThunderSubtitleItem
from .util import ensure_unique_path, sanitize_component


def apply_filters(
    items: list[ThunderSubtitleItem],
    *,
    min_score: Optional[float] = None,
    lang: Optional[str] = None,
) -> list[ThunderSubtitleItem]:
    out = items
    if min_score is not None:
        out = [i for i in out if i.score >= min_score]
    if lang:
        out = [i for i in out if lang in (i.languages or [])]
    return out


def format_item_label(item: ThunderSubtitleItem) -> str:
    langs = ",".join([x for x in (item.languages or []) if x])
    lang_part = f" lang={langs}" if langs else ""
    extra = f" {item.extra_name}".rstrip() if item.extra_name else ""
    return f"[{item.score:0.2f}] {item.name} ({item.ext}){extra}{lang_part}"


def resolve_out_dir(input_str: str | None, *, default: str = "./subs") -> Path:
    s = (input_str or "").strip()
    if not s:
        s = default
    return Path(s).expanduser()


async def search_items(
    *,
    query: str,
    limit: int = 20,
    min_score: Optional[float] = None,
    lang: Optional[str] = None,
    timeout_s: float = 20.0,
) -> list[ThunderSubtitleItem]:
    client = ThunderClient()
    items = await client.search(query=query, timeout_s=timeout_s)
    items = sorted(items, key=lambda x: x.score, reverse=True)
    items = apply_filters(items, min_score=min_score, lang=lang)
    return items[:limit]


async def download_item(
    *,
    item: ThunderSubtitleItem,
    out_dir: Path,
    timeout_s: float = 60.0,
    retries: int = 2,
    overwrite: bool = False,
) -> Path:
    client = ThunderClient()

    safe_name = sanitize_component(item.name, max_len=120)
    ext = sanitize_component(item.ext or "srt", max_len=10)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{safe_name}.{ext}"
    if not overwrite:
        path = ensure_unique_path(path)

    data = await download_with_retries(client, url=item.url, timeout_s=timeout_s, retries=retries)
    path.write_bytes(data)
    return path

