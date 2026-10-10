"""Non-blocking execution of seqtk through QProcess.

stdout can either be streamed into the result pane or written straight to a
file, which is the GUI equivalent of the shell's ``>`` redirection and keeps
multi-gigabyte FASTA output out of memory.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QProcess, Signal, Slot

# seqtk writes plain ASCII; UTF-8 with replacement keeps any stray byte visible
# instead of aborting the read.
_DECODING = "utf-8"


def _reserve_part(target: Path) -> Path:
    """Claim a staging path that provably belongs to this run.

    A fixed name such as ``out.fa.part`` can collide with a file the user
    already owns, which QProcess would then truncate and promote over the real
    destination. ``mkstemp`` creates the file exclusively, so the name is both
    unique and ours.
    """
    handle, name = tempfile.mkstemp(dir=str(target.parent), prefix=target.name + ".",
                                    suffix=".part")
    os.close(handle)
    return Path(name)


class SeqtkRunner(QObject):
    stdout_chunk = Signal(str)
    stderr_chunk = Signal(str)
    started = Signal(list)             # argv that was launched
    finished = Signal(int, str)        # exit code, one-line status id
    failed_to_start = Signal(str, str)  # error id, untranslated technical detail
    output_problem = Signal(str, str)  # error id, untranslated path detail
    state_changed = Signal(bool)       # running?

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._process: Optional[QProcess] = None
        self._start_reported = False
        self._output_target: Optional[Path] = None
        self._output_part: Optional[Path] = None

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.state() != QProcess.NotRunning

    def start(self, binary: Path | str, argv: list[str], working_dir: Optional[str] = None,
              output_file: Optional[Path | str] = None) -> bool:
        if self.running:
            return False
        self._start_reported = False
        process = QProcess(self)
        process.setProgram(str(binary))
        process.setArguments(argv)
        if working_dir:
            process.setWorkingDirectory(working_dir)
        process.setProcessChannelMode(QProcess.SeparateChannels)
        process.readyReadStandardOutput.connect(self._on_stdout)
        process.readyReadStandardError.connect(self._on_stderr)
        process.finished.connect(self._on_finished)
        process.errorOccurred.connect(self._on_error)

        if output_file is not None:
            target = Path(output_file)
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                part = _reserve_part(target)
                # Writing straight to the destination would truncate it before
                # seqtk produces a single byte, so a failed or stopped run would
                # take an existing file with it. The sidecar is promoted only
                # after a clean exit, which reproduces `>` without the loss.
                process.setStandardOutputFile(str(part), QProcess.Truncate)
                self._output_target, self._output_part = target, part
            except OSError as exc:
                # An unusable destination must not escape as an unhandled
                # exception out of the Run button.
                process.deleteLater()
                self._report_failure("run.cannot_create_output", f"{target}: {exc}")
                return False
        self._process = process
        process.start(QProcess.ReadWrite)
        if not process.waitForStarted(5000):
            process.deleteLater()
            self._discard_part()
            self._report_failure("run.failed_to_start", f"{binary}: could not be launched")
            return False
        self.state_changed.emit(True)
        self.started.emit(argv)
        return True

    def _report_failure(self, error_id: str, detail: str) -> None:
        """Emit the start failure exactly once.

        ``errorOccurred`` fires while ``waitForStarted()`` is still running, so
        both paths report the same problem and the second one is dropped.
        """
        if self._start_reported:
            return
        self._start_reported = True
        self._process = None
        self._discard_part()
        self.failed_to_start.emit(error_id, detail)
        self.state_changed.emit(False)

    def stop(self) -> None:
        if self._process is None or not self.running:
            return
        self._process.kill()

    @Slot()
    def _on_stdout(self) -> None:
        if self._process is None:
            return
        data = bytes(self._process.readAllStandardOutput().data())
        if data:
            self.stdout_chunk.emit(data.decode(_DECODING, errors="replace"))

    @Slot()
    def _on_stderr(self) -> None:
        if self._process is None:
            return
        data = bytes(self._process.readAllStandardError().data())
        if data:
            self.stderr_chunk.emit(data.decode(_DECODING, errors="replace"))

    @Slot(int, QProcess.ExitStatus)
    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        self._drain()
        stage_error = self._promote_part(exit_status == QProcess.NormalExit and exit_code == 0)
        self.state_changed.emit(False)
        if exit_status == QProcess.CrashExit:
            self.finished.emit(-1, "run.crashed")
        elif exit_code == 0:
            # A result that never reached the destination is not a success, even
            # though seqtk itself exited cleanly.
            self.finished.emit(0, stage_error or "run.ok")
        else:
            self.finished.emit(exit_code, "run.nonzero")
        if self._process is not None:
            self._process.deleteLater()
            self._process = None

    def _promote_part(self, succeeded: bool) -> Optional[str]:
        """Move the staged stdout onto the destination, or throw it away.

        Returns the id of the problem when the file system refused, else None.
        """
        part, target = self._output_part, self._output_target
        self._output_part = self._output_target = None
        if part is None or target is None:
            return None
        try:
            if succeeded:
                os.replace(part, target)
            elif part.exists():
                part.unlink()
        except OSError as exc:
            key = "run.output_save_failed" if succeeded else "run.output_cleanup_failed"
            self.output_problem.emit(key, f"{target}: {exc}")
            return key
        return None

    def _discard_part(self) -> None:
        part = self._output_part
        self._output_part = self._output_target = None
        if part is None:
            return
        try:
            if part.exists():
                part.unlink()
        except OSError as exc:
            self.output_problem.emit("run.output_cleanup_failed", f"{part}: {exc}")

    @Slot(QProcess.ProcessError)
    def _on_error(self, error: QProcess.ProcessError) -> None:
        # The enum member is Timedout (lower-case 'o'); spelling it TimedOut made
        # this slot raise AttributeError on every failed launch.
        if error in (QProcess.FailedToStart, QProcess.Timedout):
            program = self._process.program() if self._process is not None else ""
            # Qt leaves the %1 placeholder in errorString() unfilled, which would
            # reach the user as a raw template. The program path is the detail
            # that actually identifies what could not be launched.
            detail = program or str(error)
            self._report_failure("run.failed_to_start", detail)

    def _drain(self) -> None:
        """Pick up whatever arrived just before the process exited."""
        if self._process is None:
            return
        out = bytes(self._process.readAllStandardOutput().data())
        err = bytes(self._process.readAllStandardError().data())
        if out:
            self.stdout_chunk.emit(out.decode(_DECODING, errors="replace"))
        if err:
            self.stderr_chunk.emit(err.decode(_DECODING, errors="replace"))
