"""Main window: command list on the left, parameter form and output on the right."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QAction, QActionGroup, QColor, QDesktopServices, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFileDialog, QHBoxLayout, QInputDialog, QLabel,
    QLineEdit, QMainWindow, QMenu, QMessageBox, QPushButton, QSplitter,
    QStatusBar, QToolBar, QVBoxLayout, QWidget,
)

from ..core import cli_build
from ..core.binary_locator import EXPECTED_VERSION, candidates, detect_version, resolve
from ..core.paths import APP_NAME, app_root
from ..core.runner import SeqtkRunner
from ..core.settings import (
    KEY_RECENT_FILES, KEY_WINDOW_GEOMETRY, KEY_WINDOW_STATE, SettingsStore,
)
from ..core.spec import (
    KIND_REGION, KIND_SEQ, KIND_SNP, SEQTK_VERSION, Command, get_command,
)
from ..i18n.catalog import LANGUAGES, LABELS, Language, localize_filter
from ..i18n.qt_catalog import apply_qt_translations
from . import icons, themes
from .about_dialog import AboutDialog
from .command_list import CommandList
from .output_panel import OutputPanel
from .param_panel import ParamPanel

INPUT_FILE_KINDS = (KIND_SEQ, KIND_REGION, KIND_SNP)

# Name filters authored for this window's dialogs. They are handed to
# ``localize_filter``, which translates the description and keeps the
# language-neutral glob list byte for byte.
FILTER_TARGET = "All files (*)"
FILTER_INPUT = "Sequence files (*.fa *.fasta *.fq *.fastq *.gz *.txt *.bed);;All files (*)"
FILTER_BINARY = "seqtk executable (seqtk.exe seqtk);;All files (*)"


class MainWindow(QMainWindow):
    def __init__(self, lang: Language, store: SettingsStore) -> None:
        super().__init__()
        self._lang = lang
        self._store = store
        self._binary: Optional[Path] = None
        self._binary_version: Optional[str] = None
        self._started_at = 0.0

        self.resize(1180, 760)
        # Below this the splitter children hit their own minimums and the run
        # bar starts crowding the output tabs.
        self.setMinimumSize(900, 560)
        self.setAcceptDrops(True)

        self._runner = SeqtkRunner(self)
        self._runner.stdout_chunk.connect(self._on_stdout)
        self._runner.stderr_chunk.connect(self._output_append_stderr)
        self._runner.started.connect(lambda _: self._status_label.setText(self._lang.tr("status.running")))
        self._runner.finished.connect(self._on_finished)
        self._runner.failed_to_start.connect(self._on_failed)
        self._runner.output_problem.connect(self._on_output_problem)
        self._runner.state_changed.connect(self._on_state)

        self._commands = CommandList(lang)
        self._params = ParamPanel(lang)
        self._output = OutputPanel(lang)
        self._status_label = QLabel("")
        self._binary_label = QLabel("")

        self._build_actions()
        self._build_menus()
        self._build_central()
        self._build_toolbar()
        self._apply_action_icons()
        self.setStatusBar(QStatusBar())
        self.statusBar().addWidget(self._status_label, 1)
        self.statusBar().addPermanentWidget(self._binary_label)

        self._commands.selected.connect(self._on_command_selected)
        self._params.values_changed.connect(self._refresh_command_line)
        lang.changed.connect(self._on_language_changed)

        self._restore_ui_state()
        self._locate_binary()
        self.retranslate()

    # ------------------------------------------------------------------ layout
    def _build_central(self) -> None:
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(8, 8, 4, 8)
        left_layout.addWidget(self._commands)
        splitter.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(4, 8, 8, 8)
        right_layout.setSpacing(6)

        forms = QSplitter(Qt.Vertical)
        forms.addWidget(self._params)
        forms.addWidget(self._output)
        forms.setStretchFactor(0, 3)
        forms.setStretchFactor(1, 2)
        # Without an explicit split the form collapses to its header only.
        forms.setSizes([500, 300])
        forms.setChildrenCollapsible(False)
        self._params.setMinimumHeight(200)
        self._output.setMinimumHeight(180)
        right_layout.addWidget(forms, 1)
        right_layout.addLayout(self._build_run_bar())

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([270, 880])
        self.setCentralWidget(splitter)

    def _build_run_bar(self):
        bar = QHBoxLayout()
        bar.setSpacing(8)

        self._to_file_check = QCheckBox()
        self._to_file_check.toggled.connect(self._on_to_file_toggled)
        self._output_path = QLineEdit()
        self._output_path.setClearButtonEnabled(True)
        self._output_path.setEnabled(False)
        self._output_path.textChanged.connect(lambda _: self._refresh_command_line())
        browse = QPushButton("…")
        browse.setFixedWidth(32)
        browse.setEnabled(False)
        browse.clicked.connect(self._choose_output_path)
        self._browse_button = browse

        self._run_button = QPushButton()
        self._run_button.setProperty("accent", True)
        self._run_button.setIconSize(QSize(16, 16))
        self._run_button.clicked.connect(self.run)
        self._stop_button = QPushButton()
        self._stop_button.setProperty("danger", True)
        self._stop_button.setIconSize(QSize(16, 16))
        self._stop_button.setEnabled(False)
        self._stop_button.clicked.connect(self._runner.stop)

        bar.addWidget(self._to_file_check)
        bar.addWidget(self._output_path, 1)
        bar.addWidget(browse)
        bar.addStretch(1)
        bar.addWidget(self._run_button)
        bar.addWidget(self._stop_button)
        return bar

    def _build_actions(self) -> None:
        def make(slot: Callable[[], None], shortcut: Optional[str] = None) -> QAction:
            action = QAction(self)
            action.triggered.connect(slot)
            if shortcut:
                action.setShortcut(QKeySequence(shortcut))
            return action

        self._act_run = make(self.run, "Ctrl+R")
        self._act_stop = make(self._runner.stop, "Esc")
        self._act_clear = make(self._clear_all, "Ctrl+L")
        self._act_copy_cmd = make(self._copy_command_line)
        self._act_open_input = make(self._open_input_file, "Ctrl+O")
        self._act_working_dir = make(self._choose_working_dir)
        self._act_exit = make(self.close, "Ctrl+Q")
        self._act_locate = make(self._choose_binary)
        self._act_about = make(self._show_about)
        self._act_docs = make(self._open_docs)
        self._act_reveal = make(self._reveal_output_file)

    def _build_menus(self) -> None:
        bar = self.menuBar()
        self._menu_file = bar.addMenu("")
        self._menu_edit = bar.addMenu("")
        self._menu_view = bar.addMenu("")
        self._menu_tools = bar.addMenu("")
        self._menu_help = bar.addMenu("")

        self._menu_file.addAction(self._act_open_input)
        self._menu_file.addAction(self._act_working_dir)
        self._menu_file.addSeparator()
        self._recent_menu = QMenu(self)
        self._menu_file.addMenu(self._recent_menu)
        self._menu_file.addSeparator()
        self._menu_file.addAction(self._act_exit)

        self._menu_edit.addAction(self._act_copy_cmd)
        self._menu_edit.addAction(self._act_reveal)
        self._menu_edit.addAction(self._act_clear)

        self._language_menu = QMenu(self)
        group = QActionGroup(self)
        group.setExclusive(True)
        self._lang_actions: dict[str, QAction] = {}
        for code in LANGUAGES:
            action = QAction(LABELS[code], self, checkable=True)
            action.triggered.connect(lambda checked, c=code: self._set_language(c))
            group.addAction(action)
            self._language_menu.addAction(action)
            self._lang_actions[code] = action

        self._theme_menu = QMenu(self)
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        self._theme_actions: dict[str, QAction] = {}
        for name in themes.THEMES:
            action = QAction("", self, checkable=True)
            action.triggered.connect(lambda checked, n=name: self._set_theme(n))
            theme_group.addAction(action)
            self._theme_menu.addAction(action)
            self._theme_actions[name] = action

        self._menu_view.addMenu(self._language_menu)
        self._menu_view.addMenu(self._theme_menu)

        self._menu_tools.addAction(self._act_locate)
        self._menu_help.addAction(self._act_docs)
        self._menu_help.addAction(self._act_about)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar(APP_NAME)
        # saveState()/restoreState() skip toolbars without an object name, so
        # the window-state round trip would silently lose this one.
        toolbar.setObjectName("main_toolbar")
        toolbar.setMovable(False)
        # Icon-only buttons would drop the words an action needs; beside-icon
        # keeps the labels the screenshots and the user guide promise.
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toolbar.addAction(self._act_run)
        toolbar.addAction(self._act_stop)
        toolbar.addSeparator()
        toolbar.addAction(self._act_open_input)
        toolbar.addSeparator()
        toolbar.addAction(self._act_clear)
        self.addToolBar(toolbar)

    # ------------------------------------------------------------------ strings
    def retranslate(self) -> None:
        lang = self._lang
        self.setWindowTitle(f"{APP_NAME} {lang.tr('app.unofficial')} - seqtk {SEQTK_VERSION}")
        self._menu_file.setTitle(lang.tr("menu.file"))
        self._menu_edit.setTitle(lang.tr("menu.edit"))
        self._menu_view.setTitle(lang.tr("menu.view"))
        self._menu_tools.setTitle(lang.tr("menu.tools"))
        self._menu_help.setTitle(lang.tr("menu.help"))
        self._recent_menu.setTitle(lang.tr("menu.recent"))
        self._language_menu.setTitle(lang.tr("menu.language"))
        self._theme_menu.setTitle(lang.tr("menu.theme"))
        for name, action in self._theme_actions.items():
            action.setText(lang.tr(f"theme.{name}"))
        self._theme_actions[self._store.theme].setChecked(True)
        self._lang_actions[self._lang.code].setChecked(True)

        for key, action in (("act.run", self._act_run), ("act.stop", self._act_stop),
                            ("act.clear", self._act_clear), ("act.open_input", self._act_open_input),
                            ("act.working_dir", self._act_working_dir), ("act.exit", self._act_exit),
                            ("act.locate_binary", self._act_locate), ("act.about", self._act_about),
                            ("act.docs", self._act_docs),
                            ("act.copy_command", self._act_copy_cmd),
                            ("act.open_output_file", self._act_reveal)):
            action.setText(lang.tr(key))

        self._run_button.setText(lang.tr("act.run"))
        self._stop_button.setText(lang.tr("act.stop"))
        self._to_file_check.setText(lang.tr("run.to_file"))
        self._output_path.setPlaceholderText(lang.tr("run.output_placeholder"))
        self._browse_button.setToolTip(lang.tr("run.browse_output"))
        command = self._params.command
        if command is not None:
            self._apply_output_mode(command)
        self._commands.retranslate()
        self._params.retranslate()
        self._output.retranslate()
        self._rebuild_recent_menu()
        self._update_binary_label()
        self._refresh_command_line()

    def _on_language_changed(self, code: str) -> None:
        self._store.language = code
        self.retranslate()

    def _set_language(self, code: str) -> None:
        self._lang.set_code(code)
        # Qt's own dialogs come from a catalog outside strings_*.json, so the
        # runtime switch has to reload it for the new language.
        apply_qt_translations(QApplication.instance(), code)

    def _set_theme(self, name: str) -> None:
        self._store.theme = name
        themes.apply_theme(QApplication.instance(), name)
        # Icons are stroked in the theme's own colors, so they are drawn again
        # for the palette that just took effect.
        self._apply_action_icons()

    def _apply_action_icons(self) -> None:
        """Redraw every action glyph in the colors of the active theme."""
        c = themes.colors(self._store.theme)
        text = QColor(c["text"])
        self._act_run.setIcon(icons.line_icon("play", QColor(c["accent"])))
        self._act_stop.setIcon(icons.line_icon("stop", QColor(c["err"])))
        self._act_open_input.setIcon(icons.line_icon("folder", text))
        self._act_clear.setIcon(icons.line_icon("trash", text))
        self._act_copy_cmd.setIcon(icons.line_icon("copy", text))
        self._act_docs.setIcon(icons.line_icon("doc", text))
        self._act_about.setIcon(icons.line_icon("info", text))
        self._run_button.setIcon(icons.line_icon("play", QColor(c["accent_text"])))
        self._stop_button.setIcon(icons.line_icon("stop", QColor(c["err"])))

    # ---------------------------------------------------------------- commands
    def _on_command_selected(self, name: str) -> None:
        previous = self._params.command
        if previous is not None:
            self._store.save_form(previous.name, self._params.save_state())
        command = get_command(name)
        self._store.last_command = name
        self._params.show_command(command, self._store.load_form(name))
        self._apply_output_mode(command)
        self._suggest_output_path(command)
        self._refresh_command_line()

    def _apply_output_mode(self, command: Command) -> None:
        """Grey out the stdout redirect for subcommands that write files themselves.

        ``split`` opens ``<prefix>.00001.fa`` and friends directly and prints
        nothing, so redirecting its stdout would only drop one extra empty file
        next to the real results.
        """
        writes_files = command.writes_files_itself
        self._to_file_check.setEnabled(not writes_files)
        if writes_files:
            self._to_file_check.setChecked(False)
            self._output_path.clear()
            self._to_file_check.setToolTip(self._lang.tr("run.to_file_self_writes"))
        else:
            self._to_file_check.setToolTip("")

    def _suggest_output_path(self, command: Command) -> None:
        if command.writes_files_itself:
            return
        base = self._working_dir()
        if not base:
            return
        values = self._params.values()
        suffix = ""
        for positional in command.positionals:
            if positional.kind == KIND_SEQ:
                text = str(values.get(cli_build.pos_key(positional.key)) or "")
                if text and text != "-":
                    suffix = Path(text).suffix or ".fa"
                    if suffix == ".gz":
                        suffix = Path(text).with_suffix("").suffix or ".fa"
                    break
        name = f"seqtk_{command.name}_output{suffix or '.txt'}"
        self._output_path.setText(str(Path(base) / name))

    def _on_to_file_toggled(self, checked: bool) -> None:
        self._output_path.setEnabled(checked)
        self._browse_button.setEnabled(checked)
        if checked and not self._output_path.text():
            command = self._params.command
            if command is not None:
                self._suggest_output_path(command)

    def _choose_output_path(self) -> None:
        suggested = self._output_path.text() or str(Path.home() / "seqtk_output.txt")
        chosen, _ = QFileDialog.getSaveFileName(self, self._lang.tr("dialog.save_output"),
                                                suggested,
                                                localize_filter(self._lang, FILTER_TARGET))
        if chosen:
            self._output_path.setText(chosen)

    def _working_dir(self) -> str:
        configured = self._store.working_dir
        if configured:
            return configured
        command = self._params.command
        if command is None:
            return ""
        values = self._params.values()
        for positional in command.positionals:
            if positional.kind == KIND_SEQ:
                text = str(values.get(cli_build.pos_key(positional.key)) or "")
                if text and text != "-":
                    return str(Path(text).parent)
        return ""

    # --------------------------------------------------------------------- run
    def run(self) -> None:
        if self._runner.running:
            return
        command = self._params.command
        if command is None:
            QMessageBox.information(self, APP_NAME, self._lang.tr("msg.no_command"))
            return
        values = self._params.values()
        problems = cli_build.validate(command, values)
        if problems:
            lines = "\n".join("- " + self._lang.tr(key, **kwargs) for key, kwargs in problems)
            QMessageBox.warning(self, self._lang.tr("msg.validation_title"), lines)
            return
        if self._binary is None:
            self._choose_binary()
            if self._binary is None:
                return

        if command.writes_files_itself and not self._confirm_split_targets(command, values):
            return

        output_file: Optional[Path] = None
        if self._to_file_check.isChecked():
            text = self._output_path.text().strip()
            if not text:
                QMessageBox.warning(self, self._lang.tr("msg.validation_title"),
                                    self._lang.tr("msg.need_output_path"))
                return
            output_file = Path(text)
            if output_file.exists() and not self._confirm_overwrite(output_file):
                return

        self._output.clear()
        self._output.set_command_line(cli_build.build_command_line(command, values, str(self._binary)))
        self._store.save_form(command.name, self._params.save_state())
        self._remember_inputs(values)

        self._started_at = time.monotonic()
        self._runner.start(self._binary, cli_build.build_argv(command, values),
                           self._working_dir() or None, output_file)

    def _remember_inputs(self, values: dict) -> None:
        changed = False
        for key, value in values.items():
            if key.startswith(cli_build.POS_PREFIX) and isinstance(value, str) and Path(value).is_file():
                self._store.push_recent_file(value)
                changed = True
        if changed:
            self._rebuild_recent_menu()

    def _confirm_overwrite(self, path: Path) -> bool:
        answer = QMessageBox.question(self, APP_NAME,
                                      self._lang.tr("msg.overwrite", path=str(path)),
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        return answer == QMessageBox.Yes

    def _confirm_split_targets(self, command: Command, values: dict) -> bool:
        """Ask before ``split`` replaces the files it writes with its own hands.

        ``split`` opens ``<prefix>.00001.fa`` itself, so the stdout redirect - and
        with it the overwrite guard that protects it - never comes into play.
        The prefix is resolved against the directory the process runs in, which
        is where seqtk's relative paths land.
        """
        prefix = str(values.get(cli_build.pos_key("prefix")) or "")
        if not prefix:
            return True
        path = Path(prefix)
        if not path.is_absolute():
            working_dir = self._working_dir()
            if working_dir:
                path = Path(working_dir) / path
        # Matched literally rather than with Path.glob: a prefix may contain
        # glob metacharacters, and seqtk names its files "<prefix>.<n>.<ext>"
        # whatever they are, so pattern semantics would miss the files to warn
        # about.
        written = re.compile(r"{}\.\d+\.[^.]+$".format(re.escape(path.name)))
        existing = sorted(str(found) for found in path.parent.iterdir()
                          if found.is_file() and written.match(found.name)) \
            if path.parent.is_dir() else []
        if not existing:
            return True
        answer = QMessageBox.question(
            self, APP_NAME,
            self._lang.tr("msg.overwrite_split", paths="\n".join(existing)),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        return answer == QMessageBox.Yes

    def _on_stdout(self, text: str) -> None:
        self._output.append_stdout(text)

    def _output_append_stderr(self, text: str) -> None:
        self._output.append_stderr(text)

    def _on_state(self, running: bool) -> None:
        self._run_button.setEnabled(not running)
        self._stop_button.setEnabled(running)
        self._act_run.setEnabled(not running)
        self._act_stop.setEnabled(running)
        if not running:
            return
        self._output.focus_tab(0)

    def _on_finished(self, exit_code: int, status_id: str) -> None:
        elapsed = time.monotonic() - self._started_at
        message = self._lang.tr("status.finished", code=exit_code, seconds=f"{elapsed:.2f}")
        if status_id != "run.ok":
            # The exit code alone reads like a success: say in words that the
            # process crashed or bailed out.
            message = f"{message} - {self._lang.tr(status_id)}"
        self._status_label.setText(message)
        self._output.note(message)
        if status_id != "run.ok":
            self._output.focus_tab(1)
        text = self._output_path.text().strip()
        if self._to_file_check.isChecked() and text:
            path = Path(text)
            if path.is_file():
                self._output.note(self._lang.tr("status.output_size", path=str(path),
                                                size=path.stat().st_size))

    def _on_failed(self, error_id: str, detail: str = "") -> None:
        message = self._lang.tr(error_id)
        if detail:
            # The technical half is a raw path/system message: translated text
            # first, machine detail after it.
            message = f"{message}\n{detail}"
        self._status_label.setText(self._lang.tr(error_id))
        self._output.append_stderr(message)
        self._output.focus_tab(1)

    def _on_output_problem(self, error_id: str, detail: str) -> None:
        """Report a staged output file that could not be kept or cleaned up."""
        message = f"{self._lang.tr(error_id)}\n{detail}" if detail else self._lang.tr(error_id)
        self._status_label.setText(message)
        self._output.append_stderr(message)
        self._output.focus_tab(1)

    def _refresh_command_line(self) -> None:
        command = self._params.command
        if command is None:
            self._output.set_command_line("")
            return
        binary = "seqtk" if self._binary is None else str(self._binary)
        self._output.set_command_line(cli_build.build_command_line(command, self._params.values(),
                                                                  binary))

    def _copy_command_line(self) -> None:
        QApplication.clipboard().setText(self._output.command_view.toPlainText())

    def _clear_all(self) -> None:
        self._output.clear()
        self._status_label.setText("")

    # ------------------------------------------------------------------- files
    def _open_input_file(self) -> None:
        chosen, _ = QFileDialog.getOpenFileName(
            self, self._lang.tr("dialog.choose_file"),
            self._working_dir() or str(Path.home()),
            localize_filter(self._lang, FILTER_INPUT))
        if chosen:
            self._set_first_input(chosen)

    def _set_first_input(self, path: str) -> None:
        command = self._params.command
        if command is None:
            return
        for positional in command.positionals:
            if positional.kind in INPUT_FILE_KINDS:
                self._params.set_field(cli_build.pos_key(positional.key), path)
                break
        self._store.push_recent_file(path)
        self._rebuild_recent_menu()
        self._refresh_command_line()

    def _choose_working_dir(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, self._lang.tr("dialog.choose_dir"),
                                                 self._store.working_dir or str(Path.home()))
        if chosen:
            self._store.working_dir = chosen
            command = self._params.command
            if command is not None:
                self._suggest_output_path(command)

    def _reveal_output_file(self) -> None:
        text = self._output_path.text().strip()
        if text and Path(text).is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(text).parent)))

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        files, rejected = self._dropped_files(event.mimeData())
        command = self._params.command
        if command is None:
            self._status_label.setText(self._lang.tr("msg.no_command"))
            event.acceptProposedAction()
            return
        slots = [positional for positional in command.positionals
                 if positional.kind in INPUT_FILE_KINDS]
        used = files[:len(slots)]
        for positional, path in zip(slots, used):
            self._params.set_field(cli_build.pos_key(positional.key), path)
            self._store.push_recent_file(path)
        self._rebuild_recent_menu()
        self._refresh_command_line()
        self._status_label.setText(self._drop_report(command.name, len(slots),
                                                    len(used), len(files), rejected))
        event.acceptProposedAction()

    def _drop_report(self, name: str, slots: int, used: int, dropped: int,
                     rejected: int) -> str:
        """One status line covering what the drop filled and what it could not."""
        messages = []
        if used:
            messages.append(self._lang.tr("drop.filled", command=name, count=used))
        if slots - used:
            messages.append(self._lang.tr("drop.incomplete", command=name,
                                          missing=slots - used))
        if dropped - used:
            messages.append(self._lang.tr("drop.extra", command=name, slots=slots,
                                          extra=dropped - used))
        if rejected:
            messages.append(self._lang.tr("drop.rejected", count=rejected))
        return "  ".join(messages)

    def _dropped_files(self, mime) -> tuple[list[str], int]:
        """Existing local files among the dropped URLs, plus the unusable count."""
        files: list[str] = []
        rejected = 0
        for url in mime.urls():
            path = self._url_to_local_path(url)
            if path and Path(path).is_file():
                files.append(path)
            else:
                rejected += 1
        return files, rejected

    @staticmethod
    def _url_to_local_path(url: QUrl) -> str:
        """A dropped URL turned into a path the file APIs accept.

        Explorer drops ``file:///C:/dir/a.fa``. Write or paste the same URL with
        one slash short and ``C:`` lands in the URL authority, so Qt reports the
        path as ``//c/dir/a.fa`` and nothing opens; the drive letter goes back
        where it belongs. Longer hosts are UNC shares and stay as they are.
        """
        local = url.toLocalFile()
        host = url.host()
        if url.scheme() == "file" and len(host) == 1 and local.startswith(f"//{host}/"):
            return f"{host.upper()}:/{local[len(host) + 3:]}"
        return local

    # ------------------------------------------------------------------ binary
    def _locate_binary(self) -> None:
        found = resolve(self._store.binary_path)
        self._binary = found
        self._binary_version = detect_version(found) if found else None

    def _choose_binary(self) -> None:
        options = [c for c in candidates(self._store.binary_path) if c.exists]
        if options:
            lines = [f"{index + 1} - {c.source}: {c.path}" for index, c in enumerate(options)]
            chosen, ok = QInputDialog.getItem(self, self._lang.tr("dialog.choose_seqtk"),
                                              self._lang.tr("dialog.seqtk_candidates"), lines, 0, False)
            if ok and chosen:
                index = int(str(chosen).split(" -")[0]) - 1
                self._store.binary_path = str(options[index].path)
                self._locate_binary()
                self._update_binary_label()
                self._refresh_command_line()
                return
        path, _ = QFileDialog.getOpenFileName(self, self._lang.tr("dialog.choose_seqtk"),
                                              str(Path.home()),
                                              localize_filter(self._lang, FILTER_BINARY))
        if path:
            self._store.binary_path = path
            self._locate_binary()
            self._update_binary_label()
            self._refresh_command_line()

    def _update_binary_label(self) -> None:
        if self._binary is None:
            self._binary_label.setText(self._lang.tr("status.binary_missing"))
            self._binary_label.setProperty("error", True)
        else:
            version = self._binary_version or self._lang.tr("status.unknown_version")
            text = self._lang.tr("status.binary", path=str(self._binary), version=version)
            if self._binary_version and self._binary_version != EXPECTED_VERSION:
                text += "  " + self._lang.tr("status.version_mismatch", expected=SEQTK_VERSION,
                                             found=self._binary_version)
            self._binary_label.setText(text)
            self._binary_label.setProperty("error", self._binary_version is not None
                                           and self._binary_version != EXPECTED_VERSION)
        self._binary_label.style().unpolish(self._binary_label)
        self._binary_label.style().polish(self._binary_label)

    # ------------------------------------------------------------------- state
    def _restore_ui_state(self) -> None:
        geometry = self._store.window_geometry
        if geometry is not None:
            self.restoreGeometry(geometry)
        state = self._store.window_state
        if state is not None:
            self.restoreState(state)
        name = self._store.last_command
        if name:
            self._commands.select(name)

    def closeEvent(self, event) -> None:  # noqa: N802
        command = self._params.command
        if command is not None:
            self._store.save_form(command.name, self._params.save_state())
        self._store.set(KEY_WINDOW_GEOMETRY, self.saveGeometry())
        self._store.set(KEY_WINDOW_STATE, self.saveState())
        if self._runner.running:
            self._runner.stop()
        event.accept()

    def _rebuild_recent_menu(self) -> None:
        self._recent_menu.clear()
        files = self._store.recent_files
        if not files:
            empty = self._recent_menu.addAction(self._lang.tr("menu.recent_empty"))
            empty.setEnabled(False)
            return
        for path in files:
            action = self._recent_menu.addAction(Path(path).name)
            action.setToolTip(path)
            action.triggered.connect(lambda checked, p=path: self._set_first_input(p))
        self._recent_menu.addSeparator()
        clear = self._recent_menu.addAction(self._lang.tr("act.clear_recent"))
        clear.triggered.connect(self._clear_recent)

    def _clear_recent(self) -> None:
        self._store.set(KEY_RECENT_FILES, "")
        self._rebuild_recent_menu()

    def _show_about(self) -> None:
        AboutDialog(self._lang, self._binary, self._binary_version, self).exec()

    def _open_docs(self) -> None:
        docs = app_root() / "docs"
        target = docs if docs.is_dir() else app_root()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))
