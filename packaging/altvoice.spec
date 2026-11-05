# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the AltVoice tray application.

Build from the repository root:

    pyinstaller --clean --noconfirm packaging/altvoice.spec

Model weights are not bundled. They live under %LOCALAPPDATA%\\AltVoice\\models
or the path configured in config.json.
"""

from pathlib import Path

project_root = Path(SPECPATH).resolve().parent.parent  # noqa: F821 - PyInstaller injects SPECPATH

a = Analysis(  # noqa: F821
    [str(project_root / "altvoice" / "__main__.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "altvoice.ui.tray",
        "altvoice.asr.qwen3",
        "altvoice.asr.firered",
        "altvoice.asr.sherpa",
        "altvoice.asr.fake",
        "altvoice.servers",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "ruff"],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AltVoice",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="AltVoice",
)
