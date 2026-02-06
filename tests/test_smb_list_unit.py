from __future__ import annotations

from pathlib import Path

from thunder_subtitle_cli.smb_list import (
    build_unc_dir,
    extract_episode_num,
    filter_and_sort_episode_files,
    match_episode_filename,
    write_episode_list,
)


def test_match_episode_filename() -> None:
    assert match_episode_filename("第0002话 变身饼干.mp4")
    assert match_episode_filename("第0123话 ABC.mp4")
    assert not match_episode_filename("第123话 少一位.mp4")
    assert not match_episode_filename("第0002话 不是mp4.mkv")
    assert not match_episode_filename("random.mp4")


def test_extract_episode_num() -> None:
    assert extract_episode_num("第0002话 变身饼干.mp4") == 2
    assert extract_episode_num("第0123话 ABC.mp4") == 123
    assert extract_episode_num("第123话 X.mp4") is None


def test_filter_and_sort_episode_files() -> None:
    names = [
        ".git",
        "第0002话 变身饼干.mp4",
        "第0001话 梦幻的城市.mp4",
        "第0001话 另一个版本.mp4",
        "第0010话 10.mp4",
        "第0002话 不要.mkv",
    ]
    out = filter_and_sort_episode_files(names)
    assert out == [
        "第0001话 另一个版本.mp4",
        "第0001话 梦幻的城市.mp4",
        "第0002话 变身饼干.mp4",
        "第0010话 10.mp4",
    ]


def test_build_unc_dir_normalizes_separators() -> None:
    assert build_unc_dir(host="h", share="s", dir_path="a/b") == r"\\h\s\a\b"
    assert build_unc_dir(host="h", share="s", dir_path=r"a\b") == r"\\h\s\a\b"
    assert build_unc_dir(host="h", share="s", dir_path="") == r"\\h\s"


def test_write_episode_list(tmp_path: Path) -> None:
    out = tmp_path / "episode_list.txt"
    write_episode_list(output_path=out, episode_files=["a.mp4", "b.mp4"])
    assert out.read_text(encoding="utf-8") == "a.mp4\nb.mp4\n"

