from __future__ import annotations

from pathlib import Path

from thunder_subtitle_cli.core import format_item_label, resolve_out_dir
from thunder_subtitle_cli.models import ThunderSubtitleItem


def _item(*, name: str = "A", ext: str = "srt", score: float = 9.9) -> ThunderSubtitleItem:
    return ThunderSubtitleItem(
        gcid="g",
        cid="c",
        url="https://example.invalid/sub",
        ext=ext,
        name=name,
        duration=0,
        languages=["zh-CN"],
        source=0,
        score=score,
        fingerprintf_score=0.0,
        extra_name="(x)",
        mt=2,
    )


def test_resolve_out_dir_default() -> None:
    assert resolve_out_dir(None, default="./subs") == Path("./subs")
    assert resolve_out_dir("", default="./subs") == Path("./subs")
    assert resolve_out_dir("   ", default="./subs") == Path("./subs")


def test_resolve_out_dir_custom() -> None:
    assert resolve_out_dir("./x", default="./subs") == Path("./x")


def test_format_item_label_contains_fields() -> None:
    s = format_item_label(_item(name="Name", ext="ass", score=1.23))
    assert "Name" in s
    assert "(ass)" in s
    assert "1.23" in s
    assert "lang=" in s

