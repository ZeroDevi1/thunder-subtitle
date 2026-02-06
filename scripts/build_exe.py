from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build thunder-subtitle executable via PyInstaller.")
    parser.add_argument(
        "--spec",
        default=str((Path(__file__).resolve().parents[1] / "packaging" / "thunder-subtitle.spec")),
        help="Path to the PyInstaller .spec file.",
    )
    args = parser.parse_args()

    spec = Path(args.spec)
    if not spec.exists():
        raise SystemExit(f"Spec file not found: {spec}")

    # Run from project root so relative paths in .spec behave the same locally and in CI.
    project_root = spec.parent.parent
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", str(spec)]
    print("[build] " + " ".join(cmd))
    subprocess.check_call(cmd, cwd=str(project_root))
    print("[build] done. See dist/ directory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
