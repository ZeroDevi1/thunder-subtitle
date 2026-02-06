from __future__ import annotations

import os
from pathlib import Path

import pytest

from thunder_subtitle_cli.smb_list import build_unc_dir, filter_and_sort_episode_files


pytestmark = pytest.mark.integration


@pytest.mark.skipif(os.environ.get("RUN_SMB_TESTS") != "1", reason="Set RUN_SMB_TESTS=1 to enable SMB integration tests.")
def test_smb_listdir_smoke() -> None:
    """
    Smoke test: can list SMB dir and find at least 0 matching episode files.
    Requires env vars: SMB_PASS (and optionally SMB_HOST/SMB_SHARE/SMB_DIR/SMB_USER).
    """
    smb_pass = os.environ.get("SMB_PASS")
    if not smb_pass:
        pytest.skip("Missing SMB_PASS")

    from smb.SMBConnection import SMBConnection

    host = os.environ.get("SMB_HOST", "192.168.0.21")
    share = os.environ.get("SMB_SHARE", "Video")
    smb_dir = os.environ.get("SMB_DIR", "动漫/哆啦A梦")
    user = os.environ.get("SMB_USER", "ZeroDevi1")

    unc_dir = build_unc_dir(host=host, share=share, dir_path=smb_dir)
    # pysmb expects POSIX-like path inside share.
    share_path = "/" + "/".join([p for p in smb_dir.replace("\\", "/").split("/") if p])

    conn = SMBConnection(
        user,
        smb_pass,
        "thunder-subtitle-cli",
        host,
        use_ntlm_v2=True,
        is_direct_tcp=True,
    )
    ok = conn.connect(host, 445)
    assert ok
    files = conn.listPath(share, share_path)
    names = [f.filename for f in files if f.filename not in (".", "..")]
    matched = filter_and_sort_episode_files(names)
    assert isinstance(matched, list)
