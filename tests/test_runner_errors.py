"""Sub-process handling in SeqtkRunner: error reporting must never raise, never
duplicate, and never let an unusable output path escape as an unhandled error.

These are regression tests for three defects found in review:
  * ``QProcess.TimedOut`` does not exist (the member is ``Timedout``), so the
    errorOccurred slot died with AttributeError on every failed launch;
  * ``failed_to_start`` was emitted twice for one failure once that was fixed;
  * ``Path.mkdir()`` for the output file raised FileNotFoundError/FileExistsError
    straight out of the Run button, which is invisible in the windowed build.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDeadlineTimer, QProcess
from PySide6.QtWidgets import QApplication

from seqtk_gui.core.runner import SeqtkRunner

_APP = None


def get_app():
    global _APP
    if _APP is None:
        _APP = QApplication.instance() or QApplication([])
    return _APP


def pump(ms: int, until=None) -> bool:
    """Spin the event loop for up to ``ms``; return early once ``until()`` is true."""
    app = get_app()
    deadline = QDeadlineTimer(ms)
    while not deadline.hasExpired():
        app.processEvents()
        if until is not None and until():
            return True
    return until() if until is not None else False


class ErrorEnumRegression(unittest.TestCase):
    """The QProcess enum members the runner relies on must really exist."""

    def test_every_process_error_member_is_handled_without_raising(self):
        runner = SeqtkRunner()
        received = []
        runner.failed_to_start.connect(lambda *a: received.append(a))
        for member in (QProcess.FailedToStart, QProcess.Timedout, QProcess.Crashed,
                       QProcess.ReadError, QProcess.WriteError, QProcess.UnknownError):
            with self.subTest(error=member):
                runner._process = None
                runner._start_reported = False
                runner._on_error(member)          # must not raise
        self.assertEqual([r[0] for r in received],
                         ["run.failed_to_start", "run.failed_to_start"],
                         "only FailedToStart and Timedout should be reported")

    def test_failed_to_start_carries_a_detail_string(self):
        runner = SeqtkRunner()
        seen = []
        runner.failed_to_start.connect(lambda error_id, detail: seen.append((error_id, detail)))
        runner._start_reported = False
        runner._on_error(QProcess.FailedToStart)
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0][0], "run.failed_to_start")
        self.assertIsInstance(seen[0][1], str)


class StartFailures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        get_app()

    def test_missing_binary_is_reported_exactly_once(self):
        runner = SeqtkRunner()
        events = []
        runner.failed_to_start.connect(lambda *a: events.append(a))
        states = []
        runner.state_changed.connect(states.append)
        started = runner.start(Path("Z:/definitely/not/here/seqtk.exe"), ["seq", "-"])
        self.assertFalse(started)
        self.assertEqual(len(events), 1, f"failure reported {len(events)} times: {events}")
        self.assertEqual(events[0][0], "run.failed_to_start")
        self.assertFalse(runner.running)
        self.assertIn(False, states)

    def test_unusable_output_path_reports_instead_of_raising(self):
        import tempfile
        scratch = Path(tempfile.mkdtemp(prefix="seqtk-gui-err-"))
        a_file = scratch / "not-a-dir"
        a_file.write_text("keep me")
        runner = SeqtkRunner()
        events = []
        runner.failed_to_start.connect(lambda *a: events.append(a))
        target = a_file / "out.fa"          # parent is a file: mkdir must fail
        try:
            started = runner.start(sys.executable, ["-c", "pass"], output_file=target)
        except OSError as exc:               # pragma: no cover - the bug being tested
            self.fail(f"start() leaked {type(exc).__name__} to the caller: {exc}")
        self.assertFalse(started)
        self.assertEqual([e[0] for e in events], ["run.cannot_create_output"])
        self.assertFalse(target.exists())
        self.assertEqual(a_file.read_text(), "keep me")

    def test_start_is_refused_while_a_job_is_running(self):
        runner = SeqtkRunner()
        first = runner.start(sys.executable, ["-c", "import time; time.sleep(20)"])
        self.assertTrue(first)
        self.assertTrue(runner.running)
        second = runner.start(sys.executable, ["-c", "import time; time.sleep(20)"])
        self.assertFalse(second, "a second concurrent run was allowed")
        runner.stop()
        pump(5000, until=lambda: not runner.running)
        self.assertFalse(runner.running)


class DecodingIsLosslessForTheReader(unittest.TestCase):
    """seqtk output is not guaranteed to be valid UTF-8; the read must survive."""

    @classmethod
    def setUpClass(cls):
        get_app()

    def test_non_utf8_bytes_do_not_abort_the_stream(self):
        runner = SeqtkRunner()
        chunks, errors, done = [], [], []
        runner.stdout_chunk.connect(chunks.append)
        runner.stderr_chunk.connect(errors.append)
        runner.finished.connect(lambda code, status: done.append((code, status)))
        script = ("import sys;"
                  "sys.stdout.buffer.write(b'>rec\\n' + bytes(range(256)) + b'\\n');"
                  "sys.stderr.buffer.write(b'\\xff\\xfe\\x80 bad bytes\\n')")
        self.assertTrue(runner.start(sys.executable, ["-c", script]))
        pump(20000, until=lambda: bool(done))
        self.assertEqual(done, [(0, "run.ok")])
        body = "".join(chunks)
        self.assertTrue(body.startswith(">rec\n"))
        # bytes 0x00-0x7F decode as themselves, 0x80-0xFF are each one U+FFFD.
        self.assertEqual(body.count("\ufffd"), 128)
        self.assertEqual(len(body), len(">rec\n") + 256 + 1)
        self.assertIn("bad bytes", "".join(errors))


if __name__ == "__main__":
    unittest.main()
