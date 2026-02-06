from __future__ import annotations

import json
from dataclasses import asdict
from typing import Sequence

from rich.console import Console
from rich.table import Table

from .models import ThunderSubtitleItem
from .util import compute_item_id


def print_search_table(items: Sequence[ThunderSubtitleItem]) -> None:
    table = Table(title="迅雷字幕列表")
    table.add_column("序号", justify="right")
    table.add_column("评分", justify="right")
    table.add_column("格式")
    table.add_column("名称")
    table.add_column("备注")
    table.add_column("语言")
    table.add_column("ID")
    for idx, it in enumerate(items):
        _id = compute_item_id(gcid=it.gcid, cid=it.cid)
        table.add_row(
            str(idx),
            f"{it.score:0.2f}",
            it.ext,
            it.name,
            it.extra_name,
            ",".join(it.languages),
            _id,
        )
    Console().print(table)


def to_json(items: Sequence[ThunderSubtitleItem]) -> str:
    payload = []
    for it in items:
        d = asdict(it)
        d["id"] = compute_item_id(gcid=it.gcid, cid=it.cid)
        payload.append(d)
    return json.dumps(payload, ensure_ascii=False, indent=2)
