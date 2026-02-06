from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")


def compute_item_id(*, gcid: str, cid: str) -> str:
    return hashlib.md5(f"{gcid}{cid}".encode("utf-8")).hexdigest()


def sanitize_component(s: str, *, max_len: int = 80) -> str:
    """
    Make a filesystem-safe single path component (no separators, no control chars).
    """
    s = _CONTROL_CHARS_RE.sub("", s).strip()
    s = s.replace("\\", "_").replace("/", "_")
    s = re.sub(r"\s+", " ", s)
    # Windows reserved characters
    s = re.sub(r'[<>:"|?*]', "_", s)
    if not s:
        s = "untitled"
    s = s[:max_len].rstrip()
    return s


def ensure_unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    for i in range(1, 10_000):
        candidate = parent / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Unable to find unique filename for: {path}")


def parse_select_spec(spec: str) -> list[int]:
    """
    Parse e.g. "1,3,5" or "1-4,9" to unique indices in ascending order.
    """
    raw = (spec or "").strip()
    if not raw:
        return []
    out: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a_str, b_str = part.split("-", 1)
            a = int(a_str.strip())
            b = int(b_str.strip())
            if a <= b:
                rng = range(a, b + 1)
            else:
                rng = range(b, a + 1)
            out.update(rng)
        else:
            out.add(int(part))
    return sorted(out)


def is_tty() -> bool:
    # questionary needs both stdin and stdout as a tty for best behavior.
    return os.isatty(0) and os.isatty(1)

