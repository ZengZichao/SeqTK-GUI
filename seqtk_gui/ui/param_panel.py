"""Dynamic parameter form built from the seqtk command spec."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox, QDoubleSpinBox, QFileDialog, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QSpinBox, QVBoxLayout, QWidget,
)

from ..core.cli_build import opt_key, pos_key
from ..core.spec import (
    FILE_FILTER_SEQ, FILE_FILTER_TABLE, KIND_KMER, KIND_NUMBER, KIND_PREFIX,
    KIND_SEQ, KIND_TEXT, Command, Option, Positional,
)
from ..i18n.catalog import Language, localize_filter
from .themes import MONO_STACK


def to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("true", "1", "yes", "on"):
        return True
    if text in ("false", "0", "no", "off", ""):
        return False
    return default


class FileChooser(QWidget):
    """Line edit with a browse button; used for every file or prefix field."""

    value_changed = Signal()

    def __init__(self, lang: Language, filter_text: str = FILE_FILTER_SEQ,
                 directory_mode: bool = False, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._lang = lang
        self._filter = filter_text
        self._directory_mode = directory_mode
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.edit = QLineEdit()
        self.edit.setClearButtonEnabled(True)
        self.edit.textChanged.connect(lambda _: self.value_changed.emit())
        browse = QPushButton("…")
        browse.setFixedWidth(32)
        browse.clicked.connect(self._browse)
        layout.addWidget(self.edit, 1)
        layout.addWidget(browse)

    def _browse(self) -> None:
        if self._directory_mode:
            chosen = QFileDialog.getExistingDirectory(
                self, self._lang.tr("dialog.choose_dir"), self.edit.text() or str(Path.home()))
        else:
            chosen, _ = QFileDialog.getOpenFileName(
                self, self._lang.tr("dialog.choose_file"),
                str(Path(self.edit.text()).parent if self.edit.text() else Path.home()),
                # The spec filter is language neutral source text: the
                # description is translated at open time, so switching language
                # while the form is built needs no rebuild.
                localize_filter(self._lang, self._filter))
        if chosen:
            self.edit.setText(chosen)

    def text(self) -> str:
        return self.edit.text().strip()

    def set_text(self, value: str) -> None:
        self.edit.setText(value)


def read_widget(widget: QWidget) -> Any:
    if isinstance(widget, QSpinBox):
        return int(widget.value())
    if isinstance(widget, QDoubleSpinBox):
        return float(widget.value())
    if isinstance(widget, FileChooser):
        return widget.text()
    if isinstance(widget, QLineEdit):
        return widget.text().strip()
    return None


def write_widget(widget: QWidget, text: str) -> None:
    if not text:
        if isinstance(widget, (QLineEdit, FileChooser)):
            widget.clear() if isinstance(widget, QLineEdit) else widget.set_text("")
        return
    if isinstance(widget, QSpinBox):
        try:
            widget.setValue(int(float(text)))
        except ValueError:
            pass
    elif isinstance(widget, QDoubleSpinBox):
        try:
            widget.setValue(float(text))
        except ValueError:
            pass
    elif isinstance(widget, FileChooser):
        widget.set_text(text)
    elif isinstance(widget, QLineEdit):
        widget.setText(text)


class ParamPanel(QWidget):
    """Builds the widgets for one subcommand from its spec and collects their values."""

    values_changed = Signal()

    def __init__(self, lang: Language, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._lang = lang
        self._command: Optional[Command] = None
        # key -> ("flag", checkbox) | ("valued", checkbox, widget) | ("field", widget)
        self._rows: dict[str, tuple] = {}
        # widget -> callable producing its current text, replayed on language change
        self._retranslate: list[tuple[QWidget, Callable[[], str]]] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.NoFrame)
        self._body = QWidget()
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(10, 8, 10, 8)
        self._body_layout.setSpacing(8)
        self._scroll.setWidget(self._body)
        outer.addWidget(self._scroll)
        self.show_command(None)

    @property
    def command(self) -> Optional[Command]:
        return self._command

    # ------------------------------------------------------------------ build
    def show_command(self, command: Optional[Command], state: Optional[dict[str, Any]] = None) -> None:
        self._command = command
        self._rows.clear()
        self._retranslate.clear()
        self._take_body()
        if command is None:
            self._body_layout.addWidget(self._muted(self._lang.tr("panel.select_command"),
                                                   lambda: self._lang.tr("panel.select_command")))
            self._body_layout.addStretch(1)
            return

        self._body_layout.addWidget(self._header(command))
        inputs = self._inputs_group(command)
        if inputs is not None:
            self._body_layout.addWidget(inputs)
        options = self._options_group(command)
        if options is not None:
            self._body_layout.addWidget(options)
        if command.notes_en or command.notes_zh:
            note = QLabel(self._note_text(command))
            note.setWordWrap(True)
            note.setProperty("help", True)
            note.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self._body_layout.addWidget(note)
            self._retranslate.append((note, lambda c=command: self._note_text(c)))
        self._body_layout.addStretch(1)
        if state:
            self.restore_state(state)

    def _take_body(self) -> None:
        while self._body_layout.count():
            item = self._body_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def _muted(self, text: str, provider: Callable[[], str]) -> QLabel:
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setProperty("muted", True)
        self._retranslate.append((label, provider))
        return label

    def _note_text(self, command: Command) -> str:
        return self._lang.pick(command.notes_en, command.notes_zh)

    def _header(self, command: Command) -> QWidget:
        wrap = QWidget()
        layout = QVBoxLayout(wrap)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        title = QLabel(command.name)
        title.setFont(QFont(MONO_STACK, 13, QFont.Bold))
        summary = QLabel(self._lang.pick(command.summary_en, command.summary_zh))
        summary.setWordWrap(True)
        summary.setProperty("muted", True)
        usage = QLabel(self.usage_line(command))
        usage.setFont(QFont(MONO_STACK, 9))
        usage.setWordWrap(True)
        usage.setTextInteractionFlags(Qt.TextSelectableByMouse)

        for widget, provider in ((summary, lambda c=command: self._lang.pick(c.summary_en, c.summary_zh)),
                                 (usage, lambda c=command: self.usage_line(c))):
            self._retranslate.append((widget, provider))
        layout.addWidget(title)
        layout.addWidget(summary)
        layout.addWidget(usage)
        return wrap

    def usage_line(self, command: Command) -> str:
        parts = [self._lang.tr("usage.prefix"), command.name]
        if command.options:
            parts.append(self._lang.tr("usage.options"))
        for positional in command.positionals:
            parts.append(self._lang.pick(positional.help_en, positional.help_zh).split("  ")[0])
        return " ".join(parts)

    def _inputs_group(self, command: Command) -> Optional[QGroupBox]:
        if not command.positionals:
            return None
        group = QGroupBox("")
        self._retranslate.append((group, lambda: self._lang.tr("panel.inputs")))
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        for positional in command.positionals:
            widget = self._positional_widget(positional)
            self._rows[pos_key(positional.key)] = ("field", widget)

            label = QLabel(self._field_name(positional))
            label.setMinimumWidth(110)
            label.setProperty("muted", True)
            label.setToolTip(self._positional_help(positional))
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)
            row_layout.addWidget(label)
            row_layout.addWidget(widget, 1)
            layout.addWidget(row)

            hint = QLabel(self._positional_help(positional))
            hint.setWordWrap(True)
            hint.setProperty("help", True)
            hint.setIndent(116)
            layout.addWidget(hint)
            self._retranslate.append((hint, lambda p=positional: self._positional_help(p)))
            self._retranslate.append((label, lambda p=positional: self._field_name(p)))
        return group

    def _field_name(self, positional: Positional) -> str:
        key = "field." + positional.key
        name = self._lang.tr(key)
        if name == key:
            name = positional.key
        return name + (" *" if positional.required else "")

    def _positional_help(self, positional: Positional) -> str:
        return self._lang.pick(positional.help_en, positional.help_zh)

    def _positional_widget(self, positional: Positional) -> QWidget:
        if positional.kind in (KIND_NUMBER, KIND_KMER, KIND_TEXT):
            edit = QLineEdit()
            edit.setClearButtonEnabled(True)
            if positional.kind == KIND_KMER:
                edit.setPlaceholderText("ACGT")
            if positional.default is not None:
                edit.setText(str(positional.default))
            edit.textChanged.connect(lambda _: self.values_changed.emit())
            return edit
        chooser = FileChooser(self._lang,
                              FILE_FILTER_SEQ if positional.kind == KIND_SEQ else FILE_FILTER_TABLE,
                              directory_mode=positional.kind == KIND_PREFIX)
        # Without this the copyable command-line preview keeps lagging behind a
        # typed or browsed file path, so what is shown is not what would run.
        chooser.value_changed.connect(self.values_changed.emit)
        return chooser

    def _options_group(self, command: Command) -> Optional[QGroupBox]:
        if not command.options:
            return None
        group = QGroupBox("")
        self._retranslate.append((group, lambda: self._lang.tr("panel.options")))
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        for option in command.options:
            layout.addWidget(self._option_row(option))
        return group

    def _option_row(self, option: Option) -> QWidget:
        wrap = QWidget()
        layout = QVBoxLayout(wrap)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        check = QCheckBox("-" + option.flag)
        check.setProperty("flag", True)
        check.setToolTip(self._option_help(option))
        widget: Optional[QWidget] = None
        if option.is_flag:
            check.toggled.connect(lambda _: self.values_changed.emit())
            self._rows[opt_key(option.flag)] = ("flag", check)
            body = check
        else:
            widget = self._value_widget(option)
            widget.setEnabled(False)
            check.toggled.connect(widget.setEnabled)
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)
            row_layout.addWidget(check)
            # Capped editors (numbers, single chars) sit next to their flag and
            # leave the rest of the row empty; only path fields want the width.
            if widget.maximumWidth() < 16777215:
                row_layout.addWidget(widget)
                row_layout.addStretch(1)
            else:
                row_layout.addWidget(widget, 1)
            self._rows[opt_key(option.flag)] = ("valued", check, widget)
            body = row
        layout.addWidget(body)

        hint = QLabel(self._option_help(option))
        hint.setWordWrap(True)
        hint.setProperty("help", True)
        hint.setIndent(22)
        layout.addWidget(hint)
        self._retranslate.append((hint, lambda o=option: self._option_help(o)))
        return wrap

    def _option_help(self, option: Option) -> str:
        return self._lang.pick(option.help_en, option.help_zh)

    def _value_widget(self, option: Option) -> QWidget:
        if option.value_kind == "int":
            spin = QSpinBox()
            low = int(option.min_value) if option.min_value is not None else -2_147_483_647
            high = int(option.max_value) if option.max_value is not None else 2_147_483_647
            spin.setRange(low, high)
            if option.default is not None:
                spin.setValue(int(option.default))
            # A number never needs the full row; the cap keeps the disabled
            # editors from reading as wide grey bands.
            spin.setMaximumWidth(180)
            spin.valueChanged.connect(lambda _: self.values_changed.emit())
            return spin
        if option.value_kind == "float":
            spin = QDoubleSpinBox()
            spin.setDecimals(6)
            low = float(option.min_value) if option.min_value is not None else 0.0
            high = float(option.max_value) if option.max_value is not None else 1_000_000.0
            spin.setRange(low, high)
            if option.default is not None:
                spin.setValue(float(option.default))
            spin.setMaximumWidth(180)
            spin.valueChanged.connect(lambda _: self.values_changed.emit())
            return spin
        if option.value_kind in ("char", "string"):
            edit = QLineEdit()
            edit.setClearButtonEnabled(True)
            if option.max_length:
                edit.setMaxLength(option.max_length)
                if option.max_length == 1:
                    edit.setMaximumWidth(120)
            if option.default is not None:
                edit.setText(str(option.default))
            edit.textChanged.connect(lambda _: self.values_changed.emit())
            return edit
        chooser = FileChooser(self._lang, option.file_filter or FILE_FILTER_SEQ)
        chooser.value_changed.connect(self.values_changed.emit)
        return chooser

    # ----------------------------------------------------------------- state io
    def values(self) -> dict[str, Any]:
        """Values in the form ``cli_build`` expects."""
        if self._command is None:
            return {}
        out: dict[str, Any] = {}
        for option in self._command.options:
            entry = self._rows.get(opt_key(option.flag))
            if entry is None:
                continue
            if entry[0] == "flag":
                out[opt_key(option.flag)] = entry[1].isChecked()
            else:
                enabled, widget = entry[1], entry[2]
                out[opt_key(option.flag)] = read_widget(widget) if enabled.isChecked() else None
        for positional in self._command.positionals:
            entry = self._rows.get(pos_key(positional.key))
            if entry is not None:
                out[pos_key(positional.key)] = read_widget(entry[1])
        return out

    def save_state(self) -> dict[str, str]:
        if self._command is None:
            return {}
        out: dict[str, str] = {}
        for key, entry in self._rows.items():
            if entry[0] == "flag":
                out[key] = "true" if entry[1].isChecked() else "false"
            elif entry[0] == "valued":
                value = read_widget(entry[2])
                out[key] = f"{'true' if entry[1].isChecked() else 'false'}|{value or ''}"
            else:
                out[key] = str(read_widget(entry[1]) or "")
        return out

    def restore_state(self, state: dict[str, Any]) -> None:
        for key, raw in state.items():
            entry = self._rows.get(key)
            if entry is None:
                continue
            text = "" if raw is None else str(raw)
            if entry[0] == "flag":
                entry[1].setChecked(to_bool(text))
            elif entry[0] == "valued":
                enabled, _, value = text.partition("|")
                entry[1].setChecked(to_bool(enabled, default=bool(value)))
                write_widget(entry[2], value)
            else:
                write_widget(entry[1], text)

    def set_field(self, key: str, text: str) -> bool:
        """Write a positional field by key; returns False when the key is unknown."""
        entry = self._rows.get(key)
        if entry is None or entry[0] != "field":
            return False
        write_widget(entry[1], text)
        return True

    def retranslate(self) -> None:
        for widget, provider in self._retranslate:
            text = provider()
            if isinstance(widget, QGroupBox):
                widget.setTitle(text)
            else:
                widget.setText(text)
