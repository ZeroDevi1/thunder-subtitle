from __future__ import annotations

from pathlib import Path

import pytest

from thunder_subtitle_cli.util import ensure_unique_path, parse_select_spec, sanitize_component


def test_parse_select_spec_basic() -> None:
    assert parse_select_spec("1,3,5") == [1, 3, 5]
    assert parse_select_spec(" 1 , 3 , 5 ") == [1, 3, 5]


def test_parse_select_spec_ranges_and_dedup() -> None:
    assert parse_select_spec("1-3,2,5") == [1, 2, 3, 5]
    assert parse_select_spec("3-1") == [1, 2, 3]


def test_sanitize_component_removes_separators_and_controls() -> None:
    assert "/" not in sanitize_component("a/b")
    assert "\\" not in sanitize_component("a\\b")
    assert sanitize_component("\x00") == "untitled"


def test_ensure_unique_path(tmp_path: Path) -> None:
    p = tmp_path / "a.srt"
    p.write_text("x", encoding="utf-8")
    p2 = ensure_unique_path(p)
    assert p2 != p
    assert p2.name.startswith("a (")

