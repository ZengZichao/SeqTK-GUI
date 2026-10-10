# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller layout for SeqTK-GUI: one self-contained executable.

    pyinstaller packaging/SeqTK-GUI.spec --noconfirm

Produces ``dist/SeqTK-GUI.exe``. The native seqtk binary and the translation
catalogs are packed inside it; on startup PyInstaller unpacks them into
``sys._MEIPASS``, which is the first location seqtk_gui/core/paths.py searches,
so the app finds its own seqtk without any user setup.

To build a folder distribution instead (faster startup, easier to inspect),
set ONEFILE=0 before running PyInstaller.
"""

import os
import sys
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent  # noqa: F821  - provided by PyInstaller
ONEFILE = os.environ.get("ONEFILE", "1") != "0"

if sys.platform == "win32":
    platform_dir, seqtk_name = "windows", "seqtk.exe"
elif sys.platform == "darwin":
    platform_dir, seqtk_name = "macos", "seqtk"
else:
    platform_dir, seqtk_name = "linux", "seqtk"

seqtk_binary = ROOT / "bin" / platform_dir / seqtk_name

datas = [(str(ROOT / "seqtk_gui" / "i18n" / "strings"), "seqtk_gui/i18n/strings")]
# License documents must accompany the packaged program: MIT asks for its notice
# in every copy of seqtk (the bundled .exe is one), and LGPL-3.0 section 4 asks
# for the license texts of the Qt libraries that are embedded here. PyInstaller
# does NOT collect these on its own - the installed PySide6 distribution carries
# no LGPL or GPL text at all - so nothing here would arrive without this
# explicit listing.
datas += [(str(ROOT / "LICENSE.txt"), "."),
          (str(ROOT / "bin" / platform_dir / "LICENSE.seqtk.txt"), "."),
          (str(ROOT / "docs" / "THIRD_PARTY_NOTICES.md"), "."),
          (str(ROOT / "docs" / "THIRD_PARTY_NOTICES.zh-CN.md"), ".")]
for _lic in sorted((ROOT / "packaging" / "licenses").glob("*.txt")):
    datas.append((str(_lic), "licenses"))
if seqtk_binary.is_file():
    datas.append((str(seqtk_binary), f"bin/{platform_dir}"))
else:
    print(f"WARNING: {seqtk_binary} is missing; the packaged app will ask the "
          f"user to locate a seqtk executable. See docs/BUILD_SEQTK.md")

hiddenimports = ["PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets"]

# Explorer, shortcuts and the taskbar read this embedded icon; the running app
# repaints the same artwork for its windows (seqtk_gui/ui/app_icon.py).
exe_icon = ROOT / "resources" / "app.ico"
if not exe_icon.is_file():
    exe_icon = None
    print("WARNING: resources/app.ico is missing; build it with "
          "scripts/make_logo.py or the executable ships without an icon.")

a = Analysis(  # noqa: F821
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "pydoc_data", "PySide6.QtWebEngineCore",
              "PySide6.QtQml", "PySide6.QtQuick"],
    noarchive=False,
)

pyz = PYZ(a.pure)  # noqa: F821

if ONEFILE:
    exe = EXE(  # noqa: F821
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="SeqTK-GUI",
        debug=False,
        strip=False,
        upx=False,
        console=False,
        icon=exe_icon,
    )
else:
    exe = EXE(  # noqa: F821
        pyz,
        a.scripts,
        exclude_binaries=True,
        name="SeqTK-GUI",
        debug=False,
        strip=False,
        upx=False,
        console=False,
        icon=exe_icon,
    )
    COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="SeqTK-GUI")  # noqa: F821
