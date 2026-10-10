"""Qt's own built-in strings, translated to match the UI language.

Message boxes, ``QFileDialog`` and ``QDialogButtonBox`` draw their text from
Qt's internal catalog, which is not part of ``strings_*.json``. Without a
``QTranslator`` the Chinese UI still shows ``Close``, ``Yes``, ``Look in:`` and
friends in English, so the packaged Qt catalog has to be loaded whenever the
language is Chinese.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QLibraryInfo, QTranslator
from PySide6.QtWidgets import QApplication

_ZH_CATALOG = "qtbase_zh_CN"

_installed: Optional[QTranslator] = None


def _candidate_dirs() -> list[str]:
    """Where ``qtbase_*.qm`` can be, when running from source and from a bundle.

    PySide6 resolves ``TranslationsPath`` against the installed package, and a
    PyInstaller onefile bundle carries the catalogs under ``_MEIPASS`` with no
    ``qt.conf`` to redirect Qt, so the packaged location has to be named here or
    the downloaded executable silently keeps Qt's English buttons.
    """
    dirs = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        dirs.append(str(Path(meipass) / "PySide6" / "translations"))
    dirs.append(QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))
    return [found for found in dirs if Path(found).is_dir()]


def apply_qt_translations(app: Optional[QApplication], code: str) -> None:
    """Install or remove Qt's Chinese catalog for the running application."""
    global _installed
    if app is None:
        return
    if _installed is not None:
        app.removeTranslator(_installed)
        _installed = None
    if code != "zh":
        return
    translator = QTranslator(app)
    for directory in _candidate_dirs():
        if translator.load(_ZH_CATALOG, directory):
            app.installTranslator(translator)
            _installed = translator
            return


def translations_dir() -> str:
    """The directory the catalogs are read from, for tests and diagnostics."""
    dirs = _candidate_dirs()
    return dirs[0] if dirs else ""

