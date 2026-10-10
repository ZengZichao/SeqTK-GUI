"""Shared test setup: importable project, seqtk binary location, no modal blocking."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from seqtk_gui.core.binary_locator import resolve  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SEQTK_BINARY = resolve()

# Every dialog the UI raises during a test is recorded here instead of shown.
DIALOG_CALLS: list[tuple[str, str]] = []


def pytest_configure(config):
    """A modal QMessageBox would block an offscreen run forever; stub them out."""
    from PySide6.QtWidgets import QMessageBox

    def _stub(kind: str, result):
        def handler(cls, *args, **kwargs):
            DIALOG_CALLS.append((kind, " | ".join(str(a) for a in args[1:])))
            return result
        return classmethod(handler)

    QMessageBox.warning = _stub("warning", QMessageBox.StandardButton.No)
    QMessageBox.information = _stub("information", QMessageBox.StandardButton.Ok)
    QMessageBox.question = _stub("question", QMessageBox.StandardButton.No)
