"""Runtime-switchable UI language, backed by two JSON catalogs.

A dictionary-based catalog is used instead of Qt .ts/.qm files so that switching
between Chinese and English takes effect immediately, without a build step for
translators and without restarting the app.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import QObject, Signal

LANGUAGES = ("zh", "en")
LABELS = {"zh": "简体中文", "en": "English"}
_STRINGS_DIR = Path(__file__).resolve().parent / "strings"

# A QFileDialog name filter reads ``Description (*.ext *.ext2)``. The glob half
# decides which files the dialog offers and is language neutral, so only the
# description is translated. The keys on the right are catalog ids; the keys on
# the left are the descriptions the filter strings are authored with.
FILTER_DESCRIPTIONS = {
    "Sequence files": "dialog.filter_seq",
    "Table files": "dialog.filter_table",
    "seqtk executable": "dialog.filter_binary",
    "All files": "dialog.filter_all",
}


def _split_filter_entry(entry: str) -> tuple[str, str]:
    """Split ``Description (*.a *.b)`` into ``("Description", " (*.a *.b)")``."""
    index = entry.rfind(" (")
    if index > 0 and entry.endswith(")"):
        return entry[:index], entry[index:]
    return entry, ""


def localize_filter(lang: "Language", name_filters: str) -> str:
    """Return ``name_filters`` with every description part in the UI language.

    Unknown descriptions are looked up as catalog ids, miss, and come back
    unchanged, so a filter that carries no translatable description still works.
    """
    parts = []
    for entry in name_filters.split(";;"):
        description, glob = _split_filter_entry(entry)
        parts.append(lang.tr(FILTER_DESCRIPTIONS.get(description, description)) + glob)
    return ";;".join(parts)


def _load(code: str) -> dict[str, str]:
    path = _STRINGS_DIR / f"strings_{code}.json"
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


class Language(QObject):
    """Singleton-ish translator. Widgets subscribe to ``changed`` to retranslate."""

    changed = Signal(str)

    def __init__(self, code: str = "zh", parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._tables = {code: _load(code) for code in LANGUAGES}
        self._code = code if code in LANGUAGES else "zh"

    @property
    def code(self) -> str:
        return self._code

    def set_code(self, code: str) -> bool:
        if code not in LANGUAGES or code == self._code:
            return False
        self._code = code
        self.changed.emit(code)
        return True

    def tr(self, key: str, **kwargs: Any) -> str:
        table = self._tables[self._code]
        text = table.get(key)
        if text is None:
            text = self._tables["en"].get(key)
        if text is None:
            return key
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError, ValueError):
                return text
        return text

    def pick(self, en: str, zh: str) -> str:
        """Choose between two inline strings - used for the seqtk spec help text."""
        return zh if self._code == "zh" else en
