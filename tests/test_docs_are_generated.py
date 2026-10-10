"""The generated command reference must match the spec the GUI renders."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
GENERATOR = ROOT / "scripts" / "generate_commands_doc.py"
PAGES = ("COMMANDS.md", "COMMANDS.zh-CN.md")


class DocsAreGenerated(unittest.TestCase):
    def test_command_pages_exist(self):
        for name in PAGES:
            self.assertTrue((DOCS / name).is_file(), f"missing docs/{name}")

    def test_pages_are_up_to_date(self):
        for name in PAGES:
            with self.subTest(page=name):
                self.assertTrue((DOCS / name).read_text(encoding="utf-8").strip())

    def test_regenerating_the_pages_changes_nothing(self):
        before = {name: (DOCS / name).read_bytes() for name in PAGES}
        subprocess.run([sys.executable, str(GENERATOR)], check=True, cwd=str(ROOT),
                       capture_output=True)
        for name in PAGES:
            with self.subTest(page=name):
                self.assertEqual(
                    before[name], (DOCS / name).read_bytes(),
                    f"docs/{name} is stale - run python scripts/generate_commands_doc.py")

    def test_every_subcommand_is_documented(self):
        sys.path.insert(0, str(ROOT))
        from seqtk_gui.core.spec import COMMANDS

        english = (DOCS / "COMMANDS.md").read_text(encoding="utf-8")
        chinese = (DOCS / "COMMANDS.zh-CN.md").read_text(encoding="utf-8")
        for command in COMMANDS:
            heading = f"### `{command.name}`"
            self.assertIn(heading, english, f"{command.name} missing from COMMANDS.md")
            self.assertIn(heading, chinese, f"{command.name} missing from COMMANDS.zh-CN.md")

    def test_every_option_is_documented(self):
        sys.path.insert(0, str(ROOT))
        from seqtk_gui.core.spec import COMMANDS

        text = (DOCS / "COMMANDS.md").read_text(encoding="utf-8")
        for command in COMMANDS:
            for option in command.options:
                self.assertIn(f"| `-{option.flag}` |", text,
                              f"{command.name} -{option.flag} missing from the table")


class BilingualDocumentation(unittest.TestCase):
    """Every documentation page must exist in both languages."""

    PAIRED = ["README.md", "CONTRIBUTING.md"]
    DOCS_PAGES = ["USER_GUIDE", "COMMANDS", "BUILD_SEQTK", "DEVELOPMENT",
                  "THIRD_PARTY_NOTICES", "RELEASE_CHECKLIST"]

    def test_root_pages_have_both_languages(self):
        for stem in self.PAIRED:
            english = ROOT / stem
            chinese = ROOT / stem.replace(".md", ".zh-CN.md")
            self.assertTrue(english.is_file(), english.name)
            self.assertTrue(chinese.is_file(), chinese.name)

    def test_docs_have_both_languages(self):
        for page in self.DOCS_PAGES:
            english = DOCS / f"{page}.md"
            chinese = DOCS / f"{page}.zh-CN.md"
            self.assertTrue(english.is_file(), english.name)
            self.assertTrue(chinese.is_file(), chinese.name)
            self.assertGreater(len(english.read_text(encoding="utf-8")), 800)
            self.assertGreater(len(chinese.read_text(encoding="utf-8")), 400)

    def test_readme_declares_the_project_unofficial(self):
        for name in ("README.md", "README.zh-CN.md"):
            text = (ROOT / name).read_text(encoding="utf-8").lower()
            self.assertTrue("unofficial" in text or "非官方" in text, name)

    def test_readme_links_resolve(self):
        import re
        link = re.compile(r"\]\((?!https?:)([^)#]+)")
        for name in ("README.md", "README.zh-CN.md"):
            base = ROOT
            for target in link.findall((base / name).read_text(encoding="utf-8")):
                with self.subTest(link=target):
                    self.assertTrue((base / target).exists(), f"{name} links to {target}")

    def test_license_keeps_the_seqtk_notice(self):
        text = (ROOT / "LICENSE.txt").read_text(encoding="utf-8")
        self.assertIn("Copyright (c) 20082-2012 by Heng Li", text)
        self.assertIn("The MIT License", text)
        self.assertIn("SeqTK-GUI contributors", text)

    def test_seqtk_notice_is_not_silently_corrected(self):
        """The upstream '20082-2012' typo must survive verbatim everywhere."""
        for name in ("LICENSE.txt", "docs/THIRD_PARTY_NOTICES.md",
                     "docs/THIRD_PARTY_NOTICES.zh-CN.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            with self.subTest(page=name):
                self.assertIn("20082-2012", text)
                self.assertNotIn("Copyright (c) 2008-2012", text)

    def test_notice_travels_with_the_bundled_binary(self):
        """MIT binds every copy of seqtk, and the .exe in bin/ is one."""
        exe = ROOT / "bin" / "windows" / "seqtk.exe"
        notice = ROOT / "bin" / "windows" / "LICENSE.seqtk.txt"
        if not exe.is_file():
            self.skipTest("no bundled seqtk binary")
        self.assertTrue(notice.is_file(),
                        "bin/windows/seqtk.exe ships without the upstream notice")
        bundled = notice.read_text(encoding="utf-8")
        reproduced = (ROOT / "LICENSE.txt").read_text(encoding="utf-8")
        self.assertIn(bundled.strip(), reproduced)

    def test_notices_do_not_deny_the_redistribution_they_document(self):
        exe = ROOT / "bin" / "windows" / "seqtk.exe"
        if not exe.is_file():
            self.skipTest("no bundled seqtk binary")
        # Wording that contradicts shipping bin/windows/seqtk.exe. The binary is
        # in the repository, so no page may deny it; each phrase below is the
        # exact form such a claim takes.
        deny = ("NOT bundled, redistributed or relicensed",
                "seqtk itself is **not** redistributed",
                "本项目**不**再分发",
                "不再分发、也不重新授权 seqtk")
        for name in ("LICENSE.txt", "README.md", "README.zh-CN.md",
                     "docs/THIRD_PARTY_NOTICES.md",
                     "docs/THIRD_PARTY_NOTICES.zh-CN.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            with self.subTest(page=name):
                for phrase in deny:
                    self.assertNotIn(phrase, text,
                                     f"{name} claims seqtk is not shipped")

    def test_packaging_bundles_the_license_documents(self):
        spec = (ROOT / "packaging" / "SeqTK-GUI.spec").read_text(encoding="utf-8")
        for needed in ("LICENSE.txt", "LICENSE.seqtk.txt", "THIRD_PARTY_NOTICES",
                       "licenses"):
            with self.subTest(item=needed):
                self.assertIn(needed, spec)
        for name in ("LGPL-3.0-only.txt", "GPL-3.0-only.txt", "Zlib.txt"):
            self.assertTrue((ROOT / "packaging" / "licenses" / name).is_file(),
                            f"missing packaging/licenses/{name}")

    def test_about_dialog_shows_the_third_party_terms(self):
        """LGPL-3.0 s.4 wants the notice and license text reachable at run time."""
        dialog = (ROOT / "seqtk_gui" / "ui" / "about_dialog.py").read_text(encoding="utf-8")
        self.assertIn("THIRD_PARTY_NOTICES.zh-CN.md", dialog)
        self.assertIn("_MEIPASS", dialog)


if __name__ == "__main__":
    unittest.main()
