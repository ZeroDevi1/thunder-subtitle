from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from smb.SMBConnection import SMBConnection


_EP_RE = re.compile(r"^第(?P<num>\d{4})话\s+.*\.mp4$", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class SmbConfig:
    host: str
    share: str
    dir_path: str
    user: str
    password: str
    output_path: Path


def match_episode_filename(name: str) -> re.Match[str] | None:
    return _EP_RE.match(name.strip())


def extract_episode_num(name: str) -> int | None:
    m = match_episode_filename(name)
    if not m:
        return None
    return int(m.group("num"))


def filter_and_sort_episode_files(names: Iterable[str]) -> list[str]:
    out: list[str] = []
    for n in names:
        if n.strip() == ".git":
            continue
        if match_episode_filename(n):
            out.append(n.strip())

    # Sort by episode number (ascending), then by full filename.
    def _key(x: str) -> tuple[int, str]:
        num = extract_episode_num(x)
        return (num if num is not None else 10**9, x)

    return sorted(out, key=_key)


def default_output_path(project_root: Path) -> Path:
    return project_root / "out" / "episode_list.txt"


def load_config(*, project_root: Path) -> SmbConfig:
    host = os.environ.get("SMB_HOST", "192.168.0.21")
    share = os.environ.get("SMB_SHARE", "Video")
    dir_path = os.environ.get("SMB_DIR", "动漫/哆啦A梦")
    user = os.environ.get("SMB_USER", "ZeroDevi1")
    password = os.environ.get("SMB_PASS", "")
    output_path = Path(os.environ.get("OUTPUT_PATH", str(default_output_path(project_root))))

    if not password:
        raise RuntimeError("Missing SMB_PASS environment variable.")

    return SmbConfig(
        host=host,
        share=share,
        dir_path=dir_path,
        user=user,
        password=password,
        output_path=output_path,
    )


def build_unc_dir(*, host: str, share: str, dir_path: str) -> str:
    # smbclient expects an UNC path like \\server\\share\\path
    parts = [p for p in re.split(r"[\\/]+", dir_path) if p]
    tail = "\\".join(parts)
    if tail:
        return f"\\\\{host}\\{share}\\{tail}"
    return f"\\\\{host}\\{share}"


def normalize_share_path(dir_path: str) -> str:
    # pysmb expects POSIX-like paths within a share.
    parts = [p for p in re.split(r"[\\/]+", dir_path) if p]
    return "/" + "/".join(parts) if parts else "/"


def smb_listdir(
    *,
    host: str,
    share: str,
    dir_path: str,
    user: str,
    password: str,
    port: int = 445,
) -> list[str]:
    """
    List entries in an SMB share directory using pysmb.
    """
    share_path = normalize_share_path(dir_path)
    conn = SMBConnection(
        user,
        password,
        "thunder-subtitle-cli",
        host,
        use_ntlm_v2=True,
        is_direct_tcp=True,
    )
    ok = conn.connect(host, port)
    if not ok:
        raise RuntimeError(f"SMB connect failed: host={host} port={port}")

    files = conn.listPath(share, share_path)
    names: list[str] = []
    for f in files:
        if f.filename in (".", ".."):
            continue
        names.append(f.filename)
    return names


def write_episode_list(*, output_path: Path, episode_files: list[str]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(episode_files) + ("\n" if episode_files else ""), encoding="utf-8")
