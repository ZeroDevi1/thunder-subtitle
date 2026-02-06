# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


# NOTE:
# - This spec lives under ./packaging/, and PyInstaller resolves relative paths
#   relative to the spec directory. Use absolute paths for reliability.
# - Avoid collect_submodules("prompt_toolkit"): it tries to import optional
#   contrib modules (e.g. SSH) that may require extra deps (asyncssh).
# PyInstaller does not define __file__ in the spec exec namespace.
# SPECPATH is the directory containing this spec file.
project_root = Path(SPECPATH).resolve().parent

hiddenimports: list[str] = []
hiddenimports += collect_submodules("questionary")
hiddenimports += collect_submodules("rich")
hiddenimports += collect_submodules("typer")
hiddenimports += ["prompt_toolkit"]


a = Analysis(
    [str(project_root / "src" / "thunder_subtitle_cli" / "__main__.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="thunder-subtitle",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
