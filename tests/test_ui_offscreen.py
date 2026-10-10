"""Offscreen UI tests: form generation, language and theme switching, run wiring."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDeadlineTimer, QEventLoop, QSettings  # noqa: E402
from PySide6.QtWidgets import QApplication, QGroupBox, QMessageBox  # noqa: E402

from conftest import DIALOG_CALLS, FIXTURES, SEQTK_BINARY  # noqa: E402
from seqtk_gui.core.cli_build import opt_key, pos_key  # noqa: E402
from seqtk_gui.core.settings import SettingsStore  # noqa: E402
from seqtk_gui.core.spec import COMMANDS, get_command  # noqa: E402
from seqtk_gui.i18n.catalog import Language  # noqa: E402
from seqtk_gui.ui import themes  # noqa: E402
from seqtk_gui.ui.main_window import MainWindow  # noqa: E402
from seqtk_gui.ui.param_panel import ParamPanel  # noqa: E402

_APP: QApplication | None = None


def get_app() -> QApplication:
    global _APP
    if _APP is None:
        _APP = QApplication.instance() or QApplication([])
    return _APP


def temp_store() -> SettingsStore:
    handle, path = tempfile.mkstemp(prefix="seqtk-gui-test-", suffix=".ini")
    os.close(handle)
    return SettingsStore(QSettings(path, QSettings.IniFormat))


def wait_for(app: QApplication, done, timeout_ms: int = 20000) -> bool:
    """Pump the event loop with a real time slice until ``done()`` turns true."""
    deadline = QDeadlineTimer(timeout_ms)
    while not done() and not deadline.hasExpired():
        app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 10)
    return done()


class FormGeneration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        get_app()
        cls.lang = Language("zh")

    def test_row_count_matches_spec_for_every_command(self):
        for command in COMMANDS:
            with self.subTest(command=command.name):
                panel = ParamPanel(self.lang)
                panel.show_command(command)
                expected = len(command.options) + len(command.positionals)
                self.assertEqual(len(panel._rows), expected)

    def test_seq_widgets_reflect_documented_defaults(self):
        panel = ParamPanel(self.lang)
        panel.show_command(get_command("seq"))
        panel.restore_state({opt_key("l"): "true|0", opt_key("q"): "false|",
                             opt_key("A"): "true",
                             pos_key("input"): "in.fq"})
        values = panel.values()
        self.assertEqual(values[opt_key("l")], 0)
        self.assertIsNone(values[opt_key("q")])
        self.assertTrue(values[opt_key("A")])
        self.assertEqual(values[pos_key("input")], "in.fq")

    def test_state_round_trip(self):
        panel = ParamPanel(self.lang)
        panel.show_command(get_command("sample"))
        panel.restore_state({opt_key("s"): "true|11", opt_key("2"): "true",
                             pos_key("input"): "a.fa", pos_key("number"): "100"})
        saved = panel.save_state()
        second = ParamPanel(self.lang)
        second.show_command(get_command("sample"))
        second.restore_state(saved)
        self.assertEqual(second.values(), panel.values())

    def test_int_and_float_widgets_use_spec_bounds(self):
        panel = ParamPanel(self.lang)
        panel.show_command(get_command("seq"))
        spin = panel._rows[opt_key("X")][2]
        self.assertEqual((spin.minimum(), spin.maximum(), spin.value()), (0, 255, 255))

    def test_retranslate_switches_every_label(self):
        lang = Language("en")
        panel = ParamPanel(lang)
        panel.show_command(get_command("seq"))
        titles_before = [group.title() for group in panel._body.findChildren(QGroupBox)]
        lang.set_code("zh")
        panel.retranslate()
        titles_after = [group.title() for group in panel._body.findChildren(QGroupBox)]
        self.assertNotEqual(titles_before, titles_after)
        self.assertIn("选项", titles_after)


class MainWindowBehaviour(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def setUp(self):
        self.store = temp_store()
        self.lang = Language("zh")
        self.window = MainWindow(self.lang, self.store)
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.app.processEvents()

    def test_title_marks_the_project_unofficial(self):
        self.assertIn("非官方", self.window.windowTitle())
        self.lang.set_code("en")
        self.assertIn("unofficial", self.window.windowTitle())

    def test_language_switch_updates_menu_and_panels(self):
        self.lang.set_code("en")
        self.app.processEvents()
        self.assertEqual(self.window._menu_file.title(), "&File")
        self.assertEqual(self.window._run_button.text(), "Run")
        self.lang.set_code("zh")
        self.assertEqual(self.window._menu_file.title(), "文件(&F)")

    def test_theme_switch_is_applied_and_persisted(self):
        for name in themes.THEMES:
            themes.apply_theme(self.app, name)
            self.window._set_theme(name)
            self.app.processEvents()
            self.assertEqual(self.store.theme, name)
        self.assertTrue(self.app.styleSheet())

    def test_selecting_a_command_builds_its_form_and_preview(self):
        self.window._commands.select("trimfq")
        self.app.processEvents()
        self.assertEqual(self.window._params.command.name, "trimfq")
        preview = self.window._output.command_view.toPlainText()
        self.assertIn("trimfq", preview)

    def test_command_line_preview_tracks_option_widgets(self):
        self.window._commands.select("seq")
        self.app.processEvents()
        panel = self.window._params
        panel.restore_state({pos_key("input"): str(FIXTURES / "sample.fq"),
                             opt_key("A"): "true", opt_key("l"): "true|60"})
        panel.values_changed.emit()
        preview = self.window._output.command_view.toPlainText()
        self.assertIn("-A", preview)
        self.assertIn("-l 60", preview)
        self.assertIn("sample.fq", preview)

    @unittest.skipUnless(SEQTK_BINARY, "needs a real seqtk executable")
    def test_run_streams_stdout_into_result_tab(self):
        self.window._commands.select("seq")
        self.app.processEvents()
        panel = self.window._params
        panel.restore_state({pos_key("input"): str(FIXTURES / "sample.fq"),
                             opt_key("A"): "true"})
        self.window._to_file_check.setChecked(False)
        self.window.run()
        wait_for(self.app, lambda: not self.window._runner.running)
        text = self.window._output.result_view.toPlainText()
        self.assertIn(">pair1/1", text)
        self.assertTrue(text.startswith(">"), text[:80])

    @unittest.skipUnless(SEQTK_BINARY, "needs a real seqtk executable")
    def test_run_writes_stdout_straight_to_a_file(self):
        target = Path(tempfile.mkdtemp(prefix="seqtk-gui-out-")) / "result.fa"
        self.window._commands.select("seq")
        self.app.processEvents()
        self.window._params.restore_state({pos_key("input"): str(FIXTURES / "sample.fq"),
                                           opt_key("A"): "true",
                                           opt_key("r"): "true",
                                           opt_key("l"): "true|60"})
        self.window._to_file_check.setChecked(True)
        self.window._output_path.setText(str(target))
        self.window.run()
        wait_for(self.app, lambda: not self.window._runner.running)
        self.assertTrue(target.is_file(), "stdout was not redirected to the chosen file")
        content = target.read_text()
        self.assertTrue(content.startswith(">"), content[:60])
        # The result pane stays empty on purpose: the data went to disk.
        self.assertNotIn(">pair1/1", self.window._output.result_view.toPlainText())
        # QProcess redirection must match the shell's `>` byte for byte.
        import subprocess
        reference = subprocess.run([str(SEQTK_BINARY), "seq", "-l", "60", "-r", "-A",
                                    str(FIXTURES / "sample.fq")],
                                   stdout=subprocess.PIPE, check=True).stdout
        self.assertEqual(reference, target.read_bytes())
        target.unlink()

    @unittest.skipUnless(SEQTK_BINARY, "needs a real seqtk executable")
    def test_seqtk_errors_reach_the_log_tab(self):
        self.window._commands.select("seq")
        self.app.processEvents()
        missing = str(Path(self.window._store.working_dir or ".") / "does-not-exist.fa")
        self.window._params.restore_state({pos_key("input"): missing})
        self.window.run()
        wait_for(self.app, lambda: not self.window._runner.running)
        log = self.window._output.log_view.toPlainText()
        self.assertIn("failed to open the input file", log)
        self.assertIn("退出码 1", self.window._status_label.text())
        self.assertEqual(self.window._output.tabs.currentIndex(), 1)

    def test_validation_blocks_an_incomplete_form(self):
        self.window._commands.select("sample")
        self.app.processEvents()
        self.window._params.restore_state({pos_key("input"): "", pos_key("number"): ""})
        before = self.window._runner.running
        self.window.run()
        self.assertEqual(self.window._runner.running, before)

    def test_run_is_refused_before_a_dash_prefixed_input_hijacks_the_options(self):
        # seqtk re-parses '-...' as an option, then waits for a stdin the GUI
        # never closes. The form must refuse it instead of hanging the run.
        self.window._commands.select("seq")
        self.app.processEvents()
        self.window._params.restore_state({pos_key("input"): "-l100"})
        DIALOG_CALLS.clear()
        self.window.run()
        self.app.processEvents()
        self.assertFalse(self.window._runner.running)
        self.assertIn("warning", [kind for kind, _ in DIALOG_CALLS])
        text = " | ".join(detail for kind, detail in DIALOG_CALLS)
        self.assertIn(self.window._lang.tr("validate.dash", field="input"), text)

    @unittest.skipUnless(SEQTK_BINARY, "needs a real seqtk executable")
    def test_declining_the_overwrite_prompt_leaves_the_file_intact(self):
        target = Path(tempfile.mkdtemp(prefix="seqtk-gui-ovr-")) / "out.fa"
        sentinel = "PRE-EXISTING RESULTS\n" * 8
        target.write_text(sentinel)
        self.window._commands.select("seq")
        self.app.processEvents()
        self.window._params.restore_state({pos_key("input"): str(FIXTURES / "sample.fq"),
                                           opt_key("A"): "true"})
        self.window._to_file_check.setChecked(True)
        self.window._output_path.setText(str(target))
        DIALOG_CALLS.clear()
        self.window.run()                     # conftest answers the prompt with No
        self.app.processEvents()
        self.assertEqual(len([1 for kind, _ in DIALOG_CALLS if kind == "question"]), 1,
                         "no overwrite confirmation was raised")
        self.assertFalse(self.window._runner.running)
        self.assertEqual(target.read_text(), sentinel, "the file was opened for writing anyway")

    @unittest.skipUnless(SEQTK_BINARY, "needs a real seqtk executable")
    def test_accepting_the_overwrite_prompt_lets_the_run_replace_the_file(self):
        target = Path(tempfile.mkdtemp(prefix="seqtk-gui-ovr-")) / "out.fa"
        target.write_text("PRE-EXISTING RESULTS\n")
        original = QMessageBox.question
        QMessageBox.question = classmethod(
            lambda cls, *args, **kwargs: QMessageBox.StandardButton.Yes)
        try:
            self.window._commands.select("seq")
            self.app.processEvents()
            self.window._params.restore_state({pos_key("input"): str(FIXTURES / "sample.fq"),
                                               opt_key("A"): "true"})
            self.window._to_file_check.setChecked(True)
            self.window._output_path.setText(str(target))
            self.window.run()
            wait_for(self.app, lambda: not self.window._runner.running)
        finally:
            QMessageBox.question = original
        self.assertNotEqual(target.read_text(), "PRE-EXISTING RESULTS\n")
        self.assertTrue(target.read_text().startswith(">pair1/1"), target.read_text()[:40])

    def test_unusable_output_path_is_reported_instead_of_raising(self):
        scratch = Path(tempfile.mkdtemp(prefix="seqtk-gui-badout-"))
        a_file = scratch / "not-a-directory.txt"
        a_file.write_text("x")
        self.window._commands.select("seq")
        self.app.processEvents()
        self.window._params.restore_state({pos_key("input"): str(FIXTURES / "sample.fq")})
        self.window._to_file_check.setChecked(True)
        self.window._output_path.setText(str(a_file / "out.fa"))
        try:
            self.window.run()
        except OSError as exc:                # pragma: no cover - unreachable once handled
            self.fail(f"Run button leaked {type(exc).__name__}: {exc}")
        self.app.processEvents()
        self.assertFalse(self.window._runner.running)
        self.assertIn(self.window._lang.tr("run.cannot_create_output"),
                      self.window._output.log_view.toPlainText())

    def test_command_line_preview_keeps_up_with_a_typed_file_path(self):
        """The copyable preview follows a path the moment it is typed in."""
        self.window._commands.select("seq")
        self.app.processEvents()
        self.window._params.set_field(pos_key("input"), "C:/tmp/my reads.fa")
        self.app.processEvents()
        preview = self.window._output.command_view.toPlainText()
        self.assertIn("my reads.fa", preview)
        self.window._commands.select("mergepe")
        self.app.processEvents()
        self.window._params.set_field(pos_key("input2"), "C:/tmp/second.fq")
        self.app.processEvents()
        self.assertIn("second.fq", self.window._output.command_view.toPlainText())

    def test_form_state_persists_per_command(self):
        self.window._commands.select("gc")
        self.app.processEvents()
        self.window._params.restore_state({pos_key("input"): "kept.fa", opt_key("w"): "true"})
        self.window._commands.select("hety")
        self.app.processEvents()
        self.window._commands.select("gc")
        self.app.processEvents()
        self.assertEqual(self.window._params.values()[pos_key("input")], "kept.fa")

    def test_binary_label_reports_the_resolved_executable(self):
        if SEQTK_BINARY is None:
            self.assertIn("未找到", self.window._binary_label.text())
        else:
            self.assertIn("1.5-r133", self.window._binary_label.text())


if __name__ == "__main__":
    unittest.main()
