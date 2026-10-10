"""stdout / stderr / command-line views."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QTabWidget, QVBoxLayout,
    QWidget,
)

from ..i18n.catalog import Language
from .themes import MONO_STACK

# Streaming gigabytes of FASTA into a QPlainTextEdit would freeze the UI, so the
# preview is capped and the user is pointed at the "write stdout to file" mode.
# The stderr pane is capped by the same ceiling: it has no redirect to fall back
# on, so the note there sends the user to a terminal instead.
MAX_PREVIEW_CHARS = 200_000


class _CopyableView(QPlainTextEdit):
    def __init__(self) -> None:
        super().__init__()
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setFont(QFont(MONO_STACK, 10))
        self.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)


class _Budget:
    """The screen share of one output stream.

    A chunk that runs past the ceiling still contributes its leading characters,
    and from that point the stream is only counted, never rendered: a preview that
    claims to show what the pane cannot hold is worse than one that says it stops.
    """

    def __init__(self) -> None:
        self.seen = 0
        self.shown = 0
        self.exhausted = False

    def take(self, text: str) -> tuple[str, bool]:
        """Return the part of ``text`` to render and whether the budget ends here."""
        self.seen += len(text)
        if self.exhausted:
            return "", False
        head = text[:MAX_PREVIEW_CHARS - self.shown]
        self.shown += len(head)
        self.exhausted = len(head) < len(text)
        return head, self.exhausted


class OutputPanel(QWidget):
    def __init__(self, lang: Language, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._lang = lang
        self._stdout = _Budget()
        self._stderr = _Budget()
        self._stdout_lines = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.tabs = QTabWidget()
        self.result_view = _CopyableView()
        self.log_view = _CopyableView()
        self.command_view = _CopyableView()
        self.tabs.addTab(self.result_view, "")
        self.tabs.addTab(self.log_view, "")
        self.tabs.addTab(self.command_view, "")
        layout.addWidget(self.tabs, 1)

        bottom = QHBoxLayout()
        bottom.setSpacing(8)
        self.summary_label = QLabel("")
        self.summary_label.setProperty("muted", True)
        bottom.addWidget(self.summary_label, 1)
        self.clear_button = QPushButton("")
        self.clear_button.clicked.connect(self.clear)
        bottom.addWidget(self.clear_button)
        self.copy_button = QPushButton("")
        self.copy_button.clicked.connect(self._copy_current)
        bottom.addWidget(self.copy_button)
        layout.addLayout(bottom)
        self.retranslate()

    # ------------------------------------------------------------------ slots
    def append_stdout(self, text: str) -> None:
        head, ran_out = self._stdout.take(text)
        self._stdout_lines += text.count("\n")
        if head:
            self.result_view.appendPlainText(head.rstrip("\n"))
        if ran_out:
            self.result_view.appendPlainText(self._lang.tr("output.truncated"))
            self.result_view.moveCursor(QTextCursor.Start)
        self._set_summary()

    def append_stderr(self, text: str) -> None:
        head, ran_out = self._stderr.take(text)
        if head:
            self.log_view.appendPlainText(head.rstrip("\n"))
        if ran_out:
            self.log_view.appendPlainText(self._lang.tr("log.truncated",
                                                        shown=self._stderr.shown,
                                                        total=self._stderr.seen))
        self.log_view.moveCursor(QTextCursor.End)

    def set_command_line(self, text: str) -> None:
        self.command_view.setPlainText(text)

    def clear(self) -> None:
        for view in (self.result_view, self.log_view, self.command_view):
            view.clear()
        self._stdout = _Budget()
        self._stderr = _Budget()
        self._stdout_lines = 0
        self._set_summary()

    def note(self, text: str) -> None:
        """A GUI-generated line in the log, kept apart from seqtk's own output."""
        self.log_view.appendPlainText(text)
        self.log_view.moveCursor(QTextCursor.End)

    def focus_tab(self, index: int) -> None:
        self.tabs.setCurrentIndex(index)

    # ------------------------------------------------------------------ helpers
    def _copy_current(self) -> None:
        view = self.tabs.currentWidget()
        if isinstance(view, QPlainTextEdit):
            view.selectAll()
            view.copy()

    def _set_summary(self) -> None:
        if self._stdout.exhausted:
            self.summary_label.setText(self._lang.tr("output.summary_truncated",
                                                     shown=self._stdout.shown,
                                                     total=self._stdout.seen,
                                                     lines=self._stdout_lines))
        else:
            self.summary_label.setText(self._lang.tr("output.summary",
                                                     chars=self._stdout.shown,
                                                     lines=self._stdout_lines))

    def retranslate(self) -> None:
        self.tabs.setTabText(0, self._lang.tr("tab.result"))
        self.tabs.setTabText(1, self._lang.tr("tab.log"))
        self.tabs.setTabText(2, self._lang.tr("tab.command"))
        self.clear_button.setText(self._lang.tr("act.clear"))
        self.copy_button.setText(self._lang.tr("act.copy"))
        self._set_summary()
