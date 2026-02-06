from __future__ import annotations

import sys
from pathlib import Path

from thunder_subtitle_cli.smb_list import (
    build_unc_dir,
    filter_and_sort_episode_files,
    load_config,
    smb_listdir,
    write_episode_list,
)


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]

    try:
        cfg = load_config(project_root=project_root)
    except Exception as e:
        print(f"[错误] {e}", file=sys.stderr)
        return 1

    unc_dir = build_unc_dir(host=cfg.host, share=cfg.share, dir_path=cfg.dir_path)

    try:
        names = smb_listdir(
            host=cfg.host,
            share=cfg.share,
            dir_path=cfg.dir_path,
            user=cfg.user,
            password=cfg.password,
        )
    except Exception as e:
        print(f"[错误] SMB 读取失败：{unc_dir}: {e}", file=sys.stderr)
        return 1

    episode_files = filter_and_sort_episode_files(names)
    write_episode_list(output_path=cfg.output_path, episode_files=episode_files)

    print(f"[完成] 匹配到 {len(episode_files)} 个文件")
    print(f"[完成] 输出路径：{cfg.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
