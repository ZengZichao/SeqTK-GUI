"""Application bootstrap: Qt app, settings, language, theme, main window."""

from __future__ import annotations

import sys
from typing import Optional

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from .core.paths import APP_NAME, ORG_NAME
from .core.settings import SettingsStore
from .i18n.catalog import Language
from .i18n.qt_catalog import apply_qt_translations
from .ui import themes
from .ui.app_icon import application_icon
from .ui.main_window import MainWindow


def create_app(argv: Optional[list[str]] = None) -> tuple[QApplication, MainWindow]:
    app = QApplication(list(argv) if argv is not None else list(sys.argv))
    app.setOrganizationName(ORG_NAME)
    app.setApplicationName(APP_NAME)
    app.setWindowIcon(application_icon())

    store = SettingsStore()
    lang = Language(store.language)
    apply_qt_translations(app, lang.code)
    themes.apply_theme(app, store.theme)

    if sys.platform == "win32":
        # Segoe UI has no CJK glyphs; YaHei keeps the Chinese UI readable.
        app.setFont(QFont("Microsoft YaHei UI", 9))

    window = MainWindow(lang, store)
    return app, window


def run(argv: Optional[list[str]] = None) -> int:
    app, window = create_app(argv)
    window.show()
    return app.exec()


def main() -> int:
    return run()
