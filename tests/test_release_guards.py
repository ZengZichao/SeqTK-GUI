"""Guards for the invariants this GUI relies on when driving seqtk.

Each case pins something the release gates depend on: numbers reach seqtk in the
form its atof reads, a failed run never damages the destination file, ``split``
confirms before replacing files it writes itself, the copied command line
re-parses to the same argv, Qt's own dialogs follow the UI language, and the
license pages quote the checksum of the binary that actually ships.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

from seqtk_gui.core import cli_build
from seqtk_gui.core.runner import SeqtkRunner
from seqtk_gui.core.spec import COMMANDS_BY_NAME

ROOT = Path(__file__).resolve().parents[1]

SAMPLE = COMMANDS_BY_NAME["sample"]
SEED = COMMANDS_BY_NAME["seq"]


def _sample_values(number: str) -> dict:
    return {cli_build.pos_key("input"): "in.fa", cli_build.pos_key("number"): number}


# --- numbers must reach seqtk in a form atof reads the same way -------------

@pytest.mark.parametrize("text", ["1_000", "nan", "inf", "1e400", "0x10", "1,5", "５", "1e", "."])
def test_ambiguous_numbers_are_rejected(text: str):
    """``float()`` accepts several of these; seqtk's atof reads 1, 0 or garbage."""
    problems = cli_build.validate(SAMPLE, _sample_values(text))
    assert ("validate.number", {"field": "number"}) in problems


@pytest.mark.parametrize("text", ["-1", "-0.5", "-inf"])
def test_a_leading_hyphen_is_blocked_before_seqtk_sees_it(text: str):
    # getopt would read any '-' argument as an option, so the run must stop here
    # whatever the value looks like numerically.
    problems = cli_build.validate(SAMPLE, _sample_values(text))
    assert problems and not [p for p in problems if p[0] == "validate.required"]


@pytest.mark.parametrize("text", ["1000", "0.25", ".5", "1e3", "+7", "1e18"])
def test_plain_decimal_numbers_are_accepted(text: str):
    problems = cli_build.validate(SAMPLE, _sample_values(text))
    assert not [p for p in problems if p[0] == "validate.number"]


@pytest.mark.parametrize("text", ["1.9e19", "1e20", "1e30", "1e308", "18446744073709551616"])
def test_numbers_beyond_a_uint64_are_rejected(text: str):
    """seqtk counts records through ``(uint64_t)(x + .499)`` (seqtk.c:1250).

    A finite value at or past 2**64 wraps to zero, so seqtk writes nothing, says
    nothing and exits 0 - which the sidecar would then promote over the user's
    real output as a successful empty run.
    """
    problems = cli_build.validate(SAMPLE, _sample_values(text))
    assert ("validate.number", {"field": "number"}) in problems


@pytest.mark.parametrize("text", ["nan", "inf", "1_000"])
def test_ambiguous_option_values_are_rejected(text: str):
    problems = cli_build.validate(SEED, {cli_build.opt_key("s"): text})
    assert ("validate.opt_number", {"flag": "s"}) in problems


# --- the copied command line must re-parse into the same arguments ----------

def _parse_win(text: str) -> list[str]:
    """Re-parse with the CommandLineToArgvW rules the copy-pasted line obeys."""
    args: list[str] = []
    i, n = 0, len(text)
    while i < n:
        while i < n and text[i].isspace():
            i += 1
        if i >= n:
            break
        arg: list[str] = []
        quoted = False
        while i < n:
            ch = text[i]
            if ch == "\\":
                j = i
                while j < n and text[j] == "\\":
                    j += 1
                run = j - i
                if j < n and text[j] == '"':
                    arg.append("\\" * (run // 2))
                    if run % 2:
                        arg.append('"')
                    else:
                        quoted = not quoted
                    i = j + 1
                    continue
                arg.append("\\" * run)
                i = j
                continue
            if ch == '"':
                quoted = not quoted
                i += 1
                continue
            if ch.isspace() and not quoted:
                break
            arg.append(ch)
            i += 1
        args.append("".join(arg))
    return args


@pytest.mark.parametrize("text", [
    "C:\\dir\\sub\\",
    "D:\\a b\\my dir\\src.fa",
    "D:\\q\\\"x.fa",
    "D:\\unicode 中文\\é\\in.fa",
    "D:\\trail\\",
    "",
])
def test_windows_quoting_round_trips_through_the_msvc_parser(text: str):
    # The displayed line is only useful if pasting it into cmd.exe reproduces the
    # very argv the GUI would have launched.
    assert _parse_win(cli_build._quote_win(text)) == [text]


@pytest.mark.parametrize("text", ["D:\\a&b.fa", "D:\\a|b.fa", "D:\\a<b.fa"])
def test_cmd_metacharacters_force_quoting(text: str):
    assert cli_build._quote_win(text).startswith('"')


# --- a failed run may not destroy the destination file ----------------------

def test_clean_exit_promotes_the_staged_file(tmp_path: Path):
    runner = SeqtkRunner()
    target = tmp_path / "out.fa"
    target.write_text("previous content", encoding="ascii")
    part = target.with_name("out.fa.part")
    part.write_text("new result", encoding="ascii")
    runner._output_target, runner._output_part = target, part

    runner._promote_part(True)

    assert target.read_text(encoding="ascii") == "new result"
    assert not part.exists()


def test_failed_run_leaves_the_existing_file_untouched(tmp_path: Path):
    runner = SeqtkRunner()
    target = tmp_path / "out.fa"
    target.write_text("previous content", encoding="ascii")
    part = target.with_name("out.fa.part")
    part.write_text("partial", encoding="ascii")
    runner._output_target, runner._output_part = target, part

    runner._promote_part(False)

    assert target.read_text(encoding="ascii") == "previous content"
    assert not part.exists()


def test_stdout_is_staged_in_a_sidecar_not_the_destination(tmp_path: Path):
    """``Truncate`` applies to the sidecar, never to the user's destination."""
    runner = SeqtkRunner()
    target = tmp_path / "out.fa"
    target.write_text("keep me", encoding="ascii")
    assert runner.start("definitely-not-a-real-program.exe", ["seq"], None, target) is False
    assert target.read_text(encoding="ascii") == "keep me"
    assert not list(tmp_path.glob("*.part"))


def test_a_part_file_the_user_already_owns_is_never_staged_in(tmp_path: Path):
    """A fixed staging name would truncate and rename the user's own file away."""
    from seqtk_gui.core.runner import _reserve_part

    target = tmp_path / "out.fa"
    theirs = tmp_path / "out.fa.part"
    theirs.write_text("PRECIOUS USER FILE", encoding="ascii")

    claimed = [_reserve_part(target) for _ in range(5)]

    assert theirs.read_text(encoding="ascii") == "PRECIOUS USER FILE"
    assert all(found.name != theirs.name for found in claimed)
    assert len({found for found in claimed}) == len(claimed)


def test_start_does_not_disturb_an_existing_part_file(tmp_path: Path):
    runner = SeqtkRunner()
    target = tmp_path / "out.fa"
    theirs = tmp_path / "out.fa.part"
    theirs.write_text("PRECIOUS USER FILE", encoding="ascii")
    assert runner.start("definitely-not-a-real-program.exe", ["seq"], None, target) is False
    assert theirs.read_text(encoding="ascii") == "PRECIOUS USER FILE"


def test_failed_promotion_is_not_reported_as_success(tmp_path: Path):
    """seqtk exiting 0 means nothing if the result never reached the file."""
    from PySide6.QtCore import QProcess

    runner = SeqtkRunner()
    seen: list[tuple[int, str]] = []
    runner.finished.connect(lambda code, key: seen.append((code, key)))
    part = tmp_path / "out.fa.part"
    part.write_text("result", encoding="ascii")
    runner._output_target = tmp_path / "gone" / "out.fa"
    runner._output_part = part

    runner._on_finished(0, QProcess.NormalExit)

    assert seen and seen[0][1] == "run.output_save_failed"
    assert part.exists(), "an undeliverable result must not be discarded"


def test_output_problem_is_reported_when_staging_fails(tmp_path: Path):
    """A result that cannot be moved into place is kept, not thrown away."""
    runner = SeqtkRunner()
    seen: list[tuple[str, str]] = []
    runner.output_problem.connect(lambda key, detail: seen.append((key, detail)))
    part = tmp_path / "out.fa.part"
    part.write_text("the result", encoding="ascii")
    runner._output_target = tmp_path / "gone" / "out.fa"
    runner._output_part = part

    runner._promote_part(True)

    assert [key for key, _ in seen] == ["run.output_save_failed"]
    assert part.read_text(encoding="ascii") == "the result"


# --- split replaces files with its own hands, so it needs its own guard -----

def _split_stub(tmp_path):
    from seqtk_gui.i18n.catalog import Language
    from seqtk_gui.ui.main_window import MainWindow

    class Stub:
        _lang = Language("en")

        def _working_dir(self) -> str:
            return str(tmp_path)

        _confirm_split_targets = MainWindow._confirm_split_targets
    return Stub()


def test_split_warns_before_replacing_files_it_writes(tmp_path, monkeypatch):
    """Names are matched literally, because a prefix may hold glob characters.

    ``a[1]out`` is an ordinary directory name to seqtk, so pattern semantics
    would look for some other file and let the replacement go unconfirmed.
    """
    from seqtk_gui.core.spec import COMMANDS_BY_NAME
    from seqtk_gui.ui import main_window as mw

    (tmp_path / "a[1]out.00001.fa").write_text("precious", encoding="ascii")
    (tmp_path / "a[1]out.backup").write_text("unrelated", encoding="ascii")
    asked: list[str] = []

    def fake_question(parent, title, text, buttons, default=None):
        asked.append(text)
        return mw.QMessageBox.No

    monkeypatch.setattr(mw.QMessageBox, "question", staticmethod(fake_question))
    values = {cli_build.pos_key("prefix"): "a[1]out", cli_build.pos_key("input"): "in.fa"}

    assert _split_stub(tmp_path)._confirm_split_targets(COMMANDS_BY_NAME["split"], values) is False
    assert "a[1]out.00001.fa" in asked[0]
    assert "a[1]out.backup" not in asked[0]
    assert (tmp_path / "a[1]out.00001.fa").read_text(encoding="ascii") == "precious"


def test_split_runs_uninterrupted_when_it_writes_nothing_yet(tmp_path, monkeypatch):
    from seqtk_gui.core.spec import COMMANDS_BY_NAME
    from seqtk_gui.ui import main_window as mw

    calls: list[str] = []
    monkeypatch.setattr(mw.QMessageBox, "question",
                        staticmethod(lambda *a, **k: calls.append("asked") or mw.QMessageBox.Yes))
    values = {cli_build.pos_key("prefix"): "brand-new", cli_build.pos_key("input"): "in.fa"}

    assert _split_stub(tmp_path)._confirm_split_targets(COMMANDS_BY_NAME["split"], values) is True
    assert calls == []


def test_split_guard_resolves_the_prefix_where_seqtk_writes(tmp_path, monkeypatch):
    """An absolute prefix must not be re-rooted onto the working directory."""
    from seqtk_gui.core.spec import COMMANDS_BY_NAME
    from seqtk_gui.ui import main_window as mw

    elsewhere = tmp_path / "wd"
    elsewhere.mkdir()
    direct = tmp_path / "deep"
    direct.mkdir()
    (direct / "chunk.00003.fa").write_text("x", encoding="ascii")
    asked: list[str] = []
    monkeypatch.setattr(mw.QMessageBox, "question",
                        staticmethod(lambda p, t, text, b, d=None: asked.append(text)
                                     or mw.QMessageBox.No))
    values = {cli_build.pos_key("prefix"): str(direct / "chunk"),
              cli_build.pos_key("input"): "in.fa"}

    assert _split_stub(tmp_path)._confirm_split_targets(COMMANDS_BY_NAME["split"], values) is False
    assert str(direct / "chunk.00003.fa") in asked[0]


@pytest.mark.parametrize("page", [
    "docs/THIRD_PARTY_NOTICES.md",
    "docs/THIRD_PARTY_NOTICES.zh-CN.md",
])
def test_notices_quote_the_hash_of_the_shipped_binary(page: str):
    digest = hashlib.sha256((ROOT / "bin" / "windows" / "seqtk.exe").read_bytes()).hexdigest()
    text = (ROOT / page).read_text(encoding="utf-8")
    assert digest in text, f"{page} does not quote the current seqtk.exe checksum"


def test_both_i18n_tables_define_every_key_used():
    tables = {code: json_load(code) for code in ("en", "zh")}
    assert set(tables["en"]) == set(tables["zh"])
    placeholders = re.compile(r"\{(\w+)\}")
    for key, english in tables["en"].items():
        chinese = tables["zh"][key]
        assert english.strip() and chinese.strip(), key
        assert sorted(placeholders.findall(english)) == sorted(placeholders.findall(chinese)), key


def json_load(code: str) -> dict:
    import json
    return json.loads((ROOT / "seqtk_gui" / "i18n" / "strings" / f"strings_{code}.json")
                      .read_text(encoding="utf-8"))


# --- the Qt built-in catalog has to load without blowing up start-up --------

def test_qt_translations_apply_in_both_languages():
    """Loading Qt's catalog must not hinge on a QLibraryInfo member name.

    That enum is spelled differently across PySide6 releases, and the English
    branch returns before the catalog is touched, so both languages are
    exercised here.
    """
    from PySide6.QtWidgets import QApplication
    from seqtk_gui.i18n.qt_catalog import apply_qt_translations

    app = QApplication.instance() or QApplication([])
    for code in ("en", "zh", "zh", "en"):
        apply_qt_translations(app, code)
    apply_qt_translations(None, "zh")


def test_zh_dialog_buttons_are_not_left_in_english():
    from pathlib import Path

    import pytest
    from PySide6.QtWidgets import QApplication, QMessageBox

    from seqtk_gui.i18n.catalog import Language
    from seqtk_gui.i18n.qt_catalog import apply_qt_translations, translations_dir

    if not (Path(translations_dir()) / "qtbase_zh_CN.qm").is_file():
        pytest.fail("PySide6 installs no qtbase_zh_CN.qm to translate Qt's own strings")
    app = QApplication.instance() or QApplication([])
    apply_qt_translations(app, "zh")
    box = QMessageBox(QMessageBox.Warning, Language("zh").tr("msg.validation_title"),
                      "body", QMessageBox.Ok | QMessageBox.Cancel)
    assert box.button(QMessageBox.Ok).text() != "OK"
    assert box.button(QMessageBox.Cancel).text() != "Cancel"
