# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the ALT-VoiceType tray application.

Build from the repository root:

    pyinstaller --clean --noconfirm packaging/altvoice.spec

Model weights are not bundled. They live under %LOCALAPPDATA%\\ALT-VoiceType\\models
or the path configured in config.json.
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

project_root = Path(SPECPATH).resolve().parent  # noqa: F821 - PyInstaller injects SPECPATH

hiddenimports = [
    "altvoice.ui.tray",
    "altvoice.asr.qwen3",
    "altvoice.asr.firered",
    "altvoice.asr.sherpa",
    "altvoice.asr.fake",
    "altvoice.servers",
    "qwen_asr",
    "huggingface_hub",
    "six",
]
# transformers uses lazy imports; qwen-asr needs AutoConfig/AutoProcessor etc.
hiddenimports += collect_submodules("transformers")

a = Analysis(  # noqa: F821
    [str(project_root / "altvoice" / "__main__.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[(str(project_root / "altvoice" / "assets"), "altvoice/assets")],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(project_root / "packaging" / "rthook_optional.py")],
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
    name="ALT-VoiceType",
    debug=False,
    icon=str(project_root / "altvoice" / "assets" / "icon.ico"),
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
    name="ALT-VoiceType",
)

