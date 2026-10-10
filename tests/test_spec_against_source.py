"""The spec module must match seqtk.c 1.5-r133 exactly.

Nothing here is transcribed by hand: the command list is read from the dispatch
chain of ``main()``, the per-command getopt strings are parsed out of the body
of the ``stk_*`` handler each command dispatches to, the documented/undocumented
split and the version come from ``usage()``, and the letters the GUI leaves out
have to be justified by a shared switch arm in the source. That keeps this
contract honest when upstream moves: the numbers below are computed, not copied.

``seqtk.c`` is not part of this repository. It is looked up in
``$SEQTK_SOURCE``, then ``../seqtk-1.5/seqtk.c``; without either the real
comparison is skipped (and the skip says so).
"""

from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

from seqtk_gui.core.spec import COMMANDS, COMMANDS_BY_NAME, SEQTK_VERSION

ROOT = Path(__file__).resolve().parents[1]
FALLBACKS = (ROOT.parent / "seqtk-1.5" / "seqtk.c", ROOT / "seqtk-1.5" / "seqtk.c")

FUNCTION_RE = re.compile(r"^(?:static\s+)?int\s+(stk_\w+|usage)\s*\([^)]*\)", re.M)
DISPATCH_RE = re.compile(r'strcmp\s*\(\s*argv\[1\]\s*,\s*"([^"]+)"\s*\)\s*==\s*0\s*\)?\s*'
                         r'return\s+(stk_\w+)\s*\(')
GETOPT_RE = re.compile(r'getopt\s*\(\s*\w+\s*,\s*\w+\s*,\s*"([^"]*)"')
CASE_RE = re.compile(r"case '(.)':\s*")
USAGE_LINE_RE = re.compile(r'fprintf\s*\(\s*stderr\s*,\s*"([^"]*)"')
VERSION_RE = re.compile(r'fprintf\s*\(\s*stderr\s*,\s*"Version:\s*([^\\"]+)')


def source_path() -> Path | None:
    """The upstream source to check against, or None when it is unavailable."""
    env = os.environ.get("SEQTK_SOURCE") or os.environ.get("SEQTK_SRC")
    if env:
        path = Path(env)
        return path if path.is_file() else None
    return next((path for path in FALLBACKS if path.is_file()), None)


SOURCE = source_path()
SKIP_WHY = ("seqtk.c not found: set SEQTK_SOURCE or place the upstream tree at "
            + ", ".join(str(path) for path in FALLBACKS))

SOURCE_TEXT = SOURCE.read_text(encoding="utf-8", errors="replace") if SOURCE else ""


def function_bodies(text: str) -> dict[str, str]:
    """Brace-matched bodies of every ``stk_*`` function and of ``usage()``."""
    bodies: dict[str, str] = {}
    for match in FUNCTION_RE.finditer(text):
        start = text.find("{", match.end())
        if start < 0:
            continue
        depth = 0
        for index in range(start, len(text)):
            char = text[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    bodies[match.group(1)] = text[start + 1:index]
                    break
    return bodies


def parse_dispatch(text: str) -> dict[str, str]:
    """command name -> handler, in the order main() tests them."""
    return {name: handler for name, handler in DISPATCH_RE.findall(text)}


def parse_getopt(text: str) -> dict[str, str]:
    """command name -> the optstring its handler passes to getopt()."""
    bodies = function_bodies(text)
    out: dict[str, str] = {}
    for name, handler in parse_dispatch(text).items():
        match = GETOPT_RE.search(bodies.get(handler, ""))
        out[name] = match.group(1) if match else ""
    return out


def parse_synonyms(text: str) -> dict[str, set[str]]:
    """Letters sharing one switch arm per command, e.g. seq's ``a``/``A``."""
    bodies = function_bodies(text)
    out: dict[str, set[str]] = {}
    for name, handler in parse_dispatch(text).items():
        aliases: set[str] = set()
        pending: list[str] = []
        for line in bodies.get(handler, "").splitlines():
            rest, labels = line.strip(), []
            while True:
                match = CASE_RE.match(rest)
                if not match:
                    break
                labels.append(match.group(1))
                rest = rest[match.end():]
            if not labels:
                continue
            pending.extend(labels)
            if rest.strip():  # the arm finally carries a statement
                if len(pending) > 1:
                    aliases.update(pending)
                pending = []
        out[name] = aliases
    return out


def parse_usage_listing(text: str) -> set[str]:
    """Commands printed by usage(); handlers reachable from main() but absent
    here are the undocumented ones."""
    body = function_bodies(text).get("usage", "")
    listed: set[str] = set()
    for literal in USAGE_LINE_RE.findall(body):
        label = re.sub(r"^Command:\s*", "", literal.strip())
        match = re.match(r"([A-Za-z][\w]*)\s{2,}", label)
        if match:
            listed.add(match.group(1))
    return listed


def parse_version(text: str) -> str:
    match = VERSION_RE.search(text)
    return match.group(1).strip() if match else ""


# Letters the GUI deliberately does not surface; each must be an arm-level
# synonym of an exposed letter, which test_omitted_letters_are_synonyms proves.
EXPECTED_OMISSIONS = {"seq": {"a"}}

VALUE_KINDS = {"int", "float", "char", "string", "file", None}


@unittest.skipUnless(SOURCE, SKIP_WHY)
class SpecMatchesSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = SOURCE
        cls.dispatch = parse_dispatch(SOURCE_TEXT)
        cls.getopt = parse_getopt(SOURCE_TEXT)
        cls.synonyms = parse_synonyms(SOURCE_TEXT)
        cls.listed = parse_usage_listing(SOURCE_TEXT)

    def test_the_source_under_test_is_the_documented_release(self):
        self.assertEqual(parse_version(SOURCE_TEXT), SEQTK_VERSION)
        self.assertEqual(SEQTK_VERSION, "1.5-r133")

    def test_command_set_matches_main_dispatch(self):
        self.assertEqual(sorted(COMMANDS_BY_NAME), sorted(self.dispatch))
        self.assertEqual(len(COMMANDS), len(self.dispatch))

    def test_options_match_getopt_exactly(self):
        for name, optstring in self.getopt.items():
            with self.subTest(command=name, source=str(self.path)):
                upstream = {ch for ch in optstring if ch.isalnum()}
                exposed = {option.flag for option in COMMANDS_BY_NAME[name].options}
                self.assertEqual(exposed | EXPECTED_OMISSIONS.get(name, set()), upstream,
                                 f"{name}: option set differs from getopt \"{optstring}\"")

    def test_omitted_letters_are_synonyms_in_the_source(self):
        for name, omitted in EXPECTED_OMISSIONS.items():
            exposed = {option.flag for option in COMMANDS_BY_NAME[name].options}
            upstream = {ch for ch in self.getopt[name] if ch.isalnum()}
            self.assertEqual(omitted, upstream - exposed, f"{name}: unexpected omissions")
            for letter in omitted:
                self.assertIn(letter, self.synonyms[name],
                              f"{name}: -{letter} is not an arm-level synonym in seqtk.c")

    def test_getopt_letter_count_is_exposed_plus_synonyms(self):
        # 24 commands and 58 options make the 82 invocations of
        # tools/probe_seqtk.py; upstream spells 59 letters because seq -a is a
        # synonym of -A. Computed here so a drift cannot pass unnoticed.
        total_letters = sum(len([ch for ch in s if ch.isalnum()]) for s in self.getopt.values())
        total_exposed = sum(len(command.options) for command in COMMANDS)
        self.assertEqual(total_letters,
                         total_exposed + sum(len(v) for v in EXPECTED_OMISSIONS.values()))

    def test_value_flags_match_getopt_colons(self):
        for name, optstring in self.getopt.items():
            takes_value = set()
            for index, ch in enumerate(optstring):
                if ch.isalnum() and index + 1 < len(optstring) and optstring[index + 1] == ":":
                    takes_value.add(ch)
            for option in COMMANDS_BY_NAME[name].options:
                if option.flag in EXPECTED_OMISSIONS.get(name, set()):
                    continue
                self.assertEqual(option.value_kind is not None, option.flag in takes_value,
                                 f"{name}: -{option.flag} value/flag mismatch")
                self.assertIn(option.value_kind, VALUE_KINDS)

    def test_every_command_has_bilingual_text(self):
        for command in COMMANDS:
            self.assertTrue(command.summary_en, command.name)
            self.assertTrue(command.summary_zh, command.name)
            self.assertTrue(command.positionals, f"{command.name} has no positional input")
            for option in command.options:
                self.assertTrue(option.help_en, f"{command.name} -{option.flag}")
                self.assertTrue(option.help_zh, f"{command.name} -{option.flag}")
            for positional in command.positionals:
                self.assertTrue(positional.help_en, f"{command.name} {positional.key}")
                self.assertTrue(positional.help_zh, f"{command.name} {positional.key}")

    def test_defaults_are_declared_for_valued_options(self):
        for command in COMMANDS:
            for option in command.valued:
                if option.default is None:
                    self.assertIn(option.value_kind, ("file", "char", "string"),
                                  f"{command.name} -{option.flag} needs a numeric default")

    def test_undocumented_commands_come_from_the_usage_listing(self):
        undocumented = {c.name for c in COMMANDS if not c.documented}
        self.assertEqual(undocumented, set(self.dispatch) - self.listed)

    def test_trimfq_does_not_expose_unimplemented_upper_q(self):
        # Upstream usage text mentions -Q, but stk_trimfq's getopt cannot accept it.
        flags = {option.flag for option in COMMANDS_BY_NAME["trimfq"].options}
        self.assertNotIn("Q", flags)
        self.assertNotIn("Q", self.getopt["trimfq"])
        self.assertTrue(COMMANDS_BY_NAME["trimfq"].notes_en)

    def test_every_valued_option_help_quotes_its_own_letter(self):
        for command in COMMANDS:
            for option in command.options:
                for text in (option.help_en, option.help_zh):
                    if option.is_flag:
                        self.assertIn(f"-{option.flag}", text, f"{command.name} -{option.flag}")
                    else:
                        self.assertTrue(text.startswith(f"-{option.flag} "),
                                        f"{command.name} -{option.flag}: {text}")


class SpecMatchesSourceWithoutSource(unittest.TestCase):
    def test_the_source_lookup_is_explained(self):
        if SOURCE:
            self.assertTrue(SOURCE.is_file())
            self.assertEqual(SOURCE.name, "seqtk.c")
        else:  # pragma: no cover - only hit on a machine without upstream
            self.assertIn("SEQTK_SOURCE", SKIP_WHY)


if __name__ == "__main__":
    unittest.main()
