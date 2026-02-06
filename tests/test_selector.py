from __future__ import annotations

from thunder_subtitle_cli.models import ThunderSubtitleItem
from thunder_subtitle_cli.selector import DeterministicSelector
from thunder_subtitle_cli.util import compute_item_id


def _item(*, gcid: str, cid: str, name: str = "n", ext: str = "srt") -> ThunderSubtitleItem:
    return ThunderSubtitleItem(
        gcid=gcid,
        cid=cid,
        url="https://example.invalid/sub",
        ext=ext,
        name=name,
        duration=0,
        languages=["zh-CN"],
        source=0,
        score=1.0,
        fingerprintf_score=0.0,
        extra_name="",
        mt=0,
    )


def test_deterministic_selector_by_indices() -> None:
    items = [_item(gcid="g1", cid="c1"), _item(gcid="g2", cid="c2")]
    sel = DeterministicSelector(indices=[1])
    out = sel.select(query="q", items=items)
    assert len(out) == 1
    assert out[0].id == compute_item_id(gcid="g2", cid="c2")


def test_deterministic_selector_by_ids() -> None:
    items = [_item(gcid="g1", cid="c1"), _item(gcid="g2", cid="c2")]
    want = compute_item_id(gcid="g1", cid="c1")
    sel = DeterministicSelector(ids=[want])
    out = sel.select(query="q", items=items)
    assert [x.id for x in out] == [want]

