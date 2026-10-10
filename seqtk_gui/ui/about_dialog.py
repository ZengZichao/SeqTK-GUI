"""About dialog: unofficial status, seqtk attribution and license text."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel, QTextBrowser,
    QVBoxLayout, QWidget,
)

from ..core.paths import APP_NAME, app_root
from ..core.spec import SEQTK_VERSION
from ..i18n.catalog import LABELS, Language
from .app_icon import application_icon

LICENSE_FILE = "LICENSE.txt"
NOTICES_FILE = {
    "en": "THIRD_PARTY_NOTICES.md",
    "zh": "THIRD_PARTY_NOTICES.zh-CN.md",
}


class AboutDialog(QDialog):
    def __init__(self, lang: Language, binary: Optional[Path], binary_version: Optional[str],
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._lang = lang
        self.setWindowTitle(lang.tr("about.title"))
        self.resize(620, 560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(application_icon().pixmap(48, 48))
        icon_label.setAlignment(Qt.AlignVCenter)
        header.addWidget(icon_label)
        header.addSpacing(6)

        names = QVBoxLayout()
        names.setSpacing(2)
        title = QLabel(f"<b>{APP_NAME}</b>")
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        names.addWidget(title)
        tagline = QLabel(lang.tr("about.tagline"))
        tagline.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        tagline.setWordWrap(True)
        names.addWidget(tagline)
        header.addLayout(names, 1)
        layout.addLayout(header)

        banner = QLabel(lang.tr("about.unofficial"))
        banner.setAlignment(Qt.AlignCenter)
        banner.setWordWrap(True)
        banner.setProperty("error", True)
        layout.addWidget(banner)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.addRow(lang.tr("about.seqtk_version"), QLabel(f"{binary_version or SEQTK_VERSION}"))
        form.addRow(lang.tr("about.binary"), QLabel(str(binary or lang.tr("status.binary_missing"))))
        form.addRow(lang.tr("about.language"), QLabel(LABELS[lang.code]))
        layout.addLayout(form)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(False)
        browser.setPlainText(_license_text(lang))
        layout.addWidget(browser, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


def _search_roots() -> list[Path]:
    """Locations the license files may live in: package temp dir, source tree."""
    roots: list[Path] = [Path(__file__).resolve().parents[2]]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.insert(0, Path(meipass))
    roots.append(app_root())
    return roots


def _read(name: str, subdirs: tuple[str, ...] = ("", "docs")) -> Optional[str]:
    for root in _search_roots():
        for sub in subdirs:
            candidate = root / sub / name if sub else root / name
            if candidate.is_file():
                return candidate.read_text(encoding="utf-8")
    return None


def _license_text(lang: Language) -> str:
    """The license texts that must travel with the program.

    LGPL-3.0 requires a prominent notice naming the libraries used and pointing
    at their license text, and MIT requires its notice in every copy of seqtk -
    including the bundled binary. Showing only the project MIT text would leave
    both duties unmet in a packaged build, so the third-party notices page for
    the current language is appended.
    """
    parts: list[str] = []
    license_body = _read(LICENSE_FILE) or _read("LICENSE")
    parts.append(license_body if license_body else lang.tr("about.license_missing"))
    notices = _read(NOTICES_FILE.get(lang.code, NOTICES_FILE["en"]))
    if notices:
        parts.append(notices)
    separator = "\n\n" + "=" * 70 + "\n\n"
    return separator.join(parts)
