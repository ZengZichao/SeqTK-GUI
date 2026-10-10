"""Both language catalogs must be complete and equally sized."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from seqtk_gui.core.spec import COMMANDS
from seqtk_gui.i18n.catalog import LANGUAGES, Language, _STRINGS_DIR

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = (ROOT / "seqtk_gui",)

TR_CALL = re.compile(r'tr\("([a-zA-Z0-9_.]+)"')
TR_FSTRING = re.compile(r'tr\(f"([a-zA-Z0-9_.{]+)"')
ACTION_TABLE = re.compile(r'\("([a-z_]+\.[a-z_]+)",\s*self\._act')
VALIDATE_IDS = re.compile(r'\("((?:validate|run)\.[a-z_]+)"')

# Keys assembled at runtime rather than written literally.
RUNTIME_KEYS = {
    "theme.light", "theme.dark",
    "run.ok", "run.nonzero", "run.crashed", "run.failed_to_start",
    "validate.required", "validate.number", "validate.kmer",
    "validate.opt_number", "validate.opt_range",
}


def _tables(code: str) -> dict[str, str]:
    with open(_STRINGS_DIR / f"strings_{code}.json", encoding="utf-8") as handle:
        return json.load(handle)


class CatalogParity(unittest.TestCase):
    def setUp(self):
        self.zh = _tables("zh")
        self.en = _tables("en")

    def test_both_languages_exist(self):
        self.assertEqual(sorted(LANGUAGES), ["en", "zh"])

    def test_key_sets_are_identical(self):
        self.assertEqual(set(self.zh), set(self.en))

    def test_no_empty_translations(self):
        for name, table in (("zh", self.zh), ("en", self.en)):
            for key, value in table.items():
                self.assertTrue(str(value).strip(), f"{name}: empty value for {key}")

    def test_placeholders_match_between_languages(self):
        pattern = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")
        for key in self.zh:
            self.assertEqual(sorted(pattern.findall(self.zh[key])),
                             sorted(pattern.findall(self.en[key])), f"placeholder drift: {key}")


class KeysUsedInCode(unittest.TestCase):
    def _used_keys(self) -> set[str]:
        used: set[str] = set()
        for directory in SOURCE_DIRS:
            for path in directory.rglob("*.py"):
                text = path.read_text(encoding="utf-8")
                used.update(TR_CALL.findall(text))
                used.update(TR_FSTRING.findall(text))
                used.update(ACTION_TABLE.findall(text))
                used.update(VALIDATE_IDS.findall(text))
        for command in COMMANDS:
            for positional in command.positionals:
                used.add(f"field.{positional.key}")
        used.update(RUNTIME_KEYS)
        return used

    def test_every_used_key_is_translated(self):
        missing = sorted(key for key in self._used_keys()
                         if key not in _tables("zh") and "{}" not in key)
        self.assertEqual(missing, [], f"untranslated keys: {missing}")

    def test_field_keys_cover_every_positional(self):
        tables = _tables("zh")
        for command in COMMANDS:
            for positional in command.positionals:
                self.assertIn(f"field.{positional.key}", tables,
                              f"{command.name}.{positional.key}")


class LanguageSwitching(unittest.TestCase):
    def test_switch_changes_lookup(self):
        lang = Language("zh")
        self.assertEqual(lang.tr("act.run"), "运行")
        lang.set_code("en")
        self.assertEqual(lang.tr("act.run"), "Run")

    def test_pick_follows_language(self):
        lang = Language("en")
        self.assertEqual(lang.pick("hello", "你好"), "hello")
        lang.set_code("zh")
        self.assertEqual(lang.pick("hello", "你好"), "你好")

    def test_unknown_key_returns_key(self):
        self.assertEqual(Language("zh").tr("nope.not.a.key"), "nope.not.a.key")

    def test_format_arguments_are_applied(self):
        lang = Language("zh")
        self.assertIn("12", lang.tr("status.output_size", path="a.txt", size=12))


if __name__ == "__main__":
    unittest.main()
