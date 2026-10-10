"""seqtk discovery, including the layout a packaged (PyInstaller) build uses."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from seqtk_gui.core import binary_locator, paths
from seqtk_gui.core.spec import SEQTK_VERSION


def _place(root: Path, platform_dir: str | None = None) -> Path:
    exe = "seqtk.exe" if paths.is_windows() else "seqtk"
    target = root / "bin" / (platform_dir or paths.current_platform_dir()) / exe
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"")
    return target


class FrozenLayout(unittest.TestCase):
    def test_onefile_build_finds_seqtk_next_to_meipass(self):
        with tempfile.TemporaryDirectory() as tmp:
            meipass = Path(tmp) / "_MEI000001"
            target = _place(meipass)
            with mock.patch.object(paths, "is_frozen", lambda: True), \
                 mock.patch.object(sys, "_MEIPASS", str(meipass), create=True), \
                 mock.patch.object(sys, "executable", str(Path(tmp) / "SeqTK-GUI.exe")), \
                 mock.patch.object(shutil, "which", lambda name: None):
                self.assertIn(target, paths.bundled_binary_candidates())
                self.assertEqual(binary_locator.resolve(), target)

    def test_wrong_platform_folder_is_not_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            meipass = Path(tmp) / "_MEI000002"
            other = "macos" if paths.current_platform_dir() != "macos" else "windows"
            _place(meipass, other)
            with mock.patch.object(paths, "is_frozen", lambda: True), \
                 mock.patch.object(sys, "_MEIPASS", str(meipass), create=True), \
                 mock.patch.object(sys, "executable", str(Path(tmp) / "SeqTK-GUI.exe")), \
                 mock.patch.object(shutil, "which", lambda name: None):
                self.assertIsNone(binary_locator.resolve())

    def test_source_layout_uses_project_root(self):
        with mock.patch.object(paths, "is_frozen", lambda: False), \
             mock.patch.object(sys, "_MEIPASS", "/nonexistent", create=True):
            candidates = paths.bundled_binary_candidates()
        self.assertEqual(candidates[0],
                         paths.app_root() / "bin" / paths.current_platform_dir()
                         / ("seqtk.exe" if paths.is_windows() else "seqtk"))


class LookupOrder(unittest.TestCase):
    def test_explicit_setting_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            chosen = Path(tmp) / "my-seqtk"
            chosen.write_bytes(b"")
            with mock.patch.object(shutil, "which", lambda name: None):
                self.assertEqual(binary_locator.resolve(str(chosen)), chosen)

    def test_path_lookup_is_the_last_resort(self):
        with tempfile.TemporaryDirectory() as tmp:
            on_path = Path(tmp) / "seqtk"
            on_path.write_bytes(b"")
            with mock.patch.object(shutil, "which", lambda name: str(on_path)), \
                 mock.patch.object(binary_locator, "bundled_binary_candidates", lambda: []):
                self.assertEqual(binary_locator.resolve(), on_path)

    def test_missing_everywhere_returns_none(self):
        with mock.patch.object(shutil, "which", lambda name: None), \
             mock.patch.object(binary_locator, "bundled_binary_candidates",
                               lambda: [Path(tempfile.gettempdir()) / "definitely-absent-seqtk"]):
            self.assertIsNone(binary_locator.resolve())

    def test_candidates_are_labelled_by_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            chosen = Path(tmp) / "seqtk.exe"
            chosen.write_bytes(b"")
            with mock.patch.object(shutil, "which", lambda name: None), \
                 mock.patch.object(binary_locator, "bundled_binary_candidates", lambda: []):
                found = binary_locator.candidates(str(chosen))
            self.assertEqual(found[0].source, "setting")
            self.assertTrue(found[0].exists)


class VersionDetection(unittest.TestCase):
    def test_unreadable_binary_returns_none(self):
        self.assertIsNone(binary_locator.detect_version(Path("Z:/no/such/seqtk")))

    def test_expected_version_matches_the_spec(self):
        self.assertEqual(binary_locator.EXPECTED_VERSION, SEQTK_VERSION)


if __name__ == "__main__":
    unittest.main()
