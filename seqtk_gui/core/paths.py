"""Platform layout.

The project ships for Windows today but every path is resolved through this
module, so adding macOS only needs a new ``PLATFORM_DIRS`` entry and a binary
drop into ``bin/macos``.
"""

from __future__ import annotations

import sys
from pathlib import Path

APP_NAME = "SeqTK-GUI"
ORG_NAME = "SeqTK-GUI"

# sys.platform -> folder under bin/ that holds the native seqtk executable.
PLATFORM_DIRS = {"win32": "windows", "darwin": "macos", "linux": "linux"}


def current_platform_dir() -> str:
    return PLATFORM_DIRS.get(sys.platform, sys.platform)


def is_windows() -> bool:
    return sys.platform == "win32"


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def app_root() -> Path:
    """Directory of the packaged executable, or of the project when running from source."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def bundled_binary_candidates() -> list[Path]:
    """Where a seqtk built for this platform may live inside the project."""
    exe = "seqtk.exe" if is_windows() else "seqtk"
    plat = current_platform_dir()
    roots: list[Path] = []
    if is_frozen():
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            roots.append(Path(meipass))
        roots.append(app_root())
    else:
        roots.append(app_root())
    out: list[Path] = []
    for root in roots:
        for rel in ((Path("bin") / plat / exe), Path("bin") / exe, Path(exe)):
            candidate = root / rel
            if candidate not in out:
                out.append(candidate)
    return out
