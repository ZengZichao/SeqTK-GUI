"""Render the main window into docs/screenshots for the README.

Uses the same bootstrap as the real app (seqtk_gui.app.create_app) so the
screenshots show the fonts, theme and layout an actual user sees. Run it from a
normal desktop session, not with QT_QPA_PLATFORM=offscreen, or CJK glyphs may
fall back to boxes.

The file paths shown inside the window are fixed placeholders (see DEMO_DIR), so
the output is identical on every machine and never reveals where it was built.

    python scripts/make_screenshots.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QSettings  # noqa: E402

from seqtk_gui.app import create_app  # noqa: E402
from seqtk_gui.core.cli_build import opt_key, pos_key  # noqa: E402
from seqtk_gui.core.settings import SettingsStore  # noqa: E402
from seqtk_gui.i18n.catalog import Language  # noqa: E402
from seqtk_gui.ui import themes  # noqa: E402
from seqtk_gui.ui.main_window import MainWindow  # noqa: E402

OUT = ROOT / "docs" / "screenshots"

# Every path rendered below is a fixed placeholder, never a real one. The images
# end up in the public README, so the machine that happens to render them must
# not be able to leave its own user folder in the picture.
DEMO_DIR = Path("C:/seqtk-demo")
SAMPLE = str(DEMO_DIR / "sample.fq")
DEMO_BINARY = DEMO_DIR / "bin" / "windows" / "seqtk.exe"
STDOUT_SAMPLE = ">pair1/1 pair one\nACGTACGTNN\n>pair2/1 pair two\nACGAAGTGCC\n"
STDERR_SAMPLE = "[W::stk_seq] example warning written by seqtk\n"


def capture(app, lang: Language, store: SettingsStore, theme: str, code: str) -> Path:
    themes.apply_theme(app, theme)
    lang.set_code(code)
    main = MainWindow(lang, store)
    # The status bar would otherwise print this machine's real seqtk.exe path.
    main._binary = DEMO_BINARY
    main._update_binary_label()
    main.resize(1200, 800)
    main._commands.select("seq")
    app.processEvents()
    main._params.restore_state({
        pos_key("input"): SAMPLE,
        opt_key("A"): "true",
        opt_key("r"): "true",
        opt_key("l"): "true|60",
    })
    main._output.set_command_line(f"seqtk seq -l 60 -r -A {SAMPLE}")
    main._output.append_stdout(STDOUT_SAMPLE)
    main._output.append_stderr(STDERR_SAMPLE)
    main.show()
    for _ in range(60):
        app.processEvents()
    target = OUT / f"{theme}-{code}.png"
    main.grab().save(str(target))
    print("wrote", target)
    main.close()
    return target


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob("*.png"):
        stale.unlink()
    app, _window = create_app([])
    store = SettingsStore(QSettings(str(Path(tempfile.mkdtemp()) / "shots.ini"),
                                    QSettings.IniFormat))
    lang = Language("zh")
    for theme_name in ("light", "dark"):
        for code in ("zh", "en"):
            capture(app, lang, store, theme_name, code)
    return 0


if __name__ == "__main__":
    sys.exit(main())
