"""End-to-end checks against a real seqtk executable.

Skipped when no seqtk binary is available. These tests are what prove the GUI's
spec is not only faithful to seqtk.c but actually accepted by the program,
including the options the upstream usage text forgets to mention.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from conftest import FIXTURES, SEQTK_BINARY
from seqtk_gui.core.spec import COMMANDS, COMMANDS_BY_NAME

BINARY = str(SEQTK_BINARY) if SEQTK_BINARY else None


def option_of(command: str, flag: str):
    """The spec Option of one subcommand, by its letter."""
    return next(o for o in COMMANDS_BY_NAME[command].options if o.flag == flag)

# Positional arguments per command. A bare name that exists under tests/fixtures
# is used as a file; "tmp:" paths are created inside a scratch directory;
# anything else is passed through as a literal argument.
POSITIONALS = {
    "seq": ["sample.fa"],
    "size": ["sample.fa"],
    "comp": ["sample.fa"],
    "sample": ["sample.fa", "1"],
    "subseq": ["sample.fa", "names.txt"],
    "fqchk": ["sample.fq"],
    "mergepe": ["sample.fq", "sample2.fq"],
    "split": ["tmp:out/part", "sample.fa"],
    "trimfq": ["sample.fq"],
    "hety": ["sample.fa"],
    "gc": ["sample.fa"],
    "mutfa": ["sample.fa", "mutations.txt"],
    "mergefa": ["sample.fa", "sample2.fa"],
    "famask": ["sample.fa", "sample2.fa"],
    "dropse": ["sample.fq"],
    "rename": ["sample.fa", "ren"],
    "randbase": ["sample.fa"],
    "cutN": ["sample.fa"],
    "gap": ["sample.fa"],
    "listhet": ["sample.fa"],
    "hpc": ["sample.fa"],
    "telo": ["sample.fa"],
    "hrun": ["sample.fa", "3"],
    "kfreq": ["AC", "sample.fa"],
}

# Values that would otherwise crash or no-op on the small fixtures
# (hety -w 2 -t 5 divides the window step through zero, for instance).
OPTION_VALUES = {
    ("hety", "w"): "10",
    ("hety", "t"): "2",
    ("split", "n"): "2",
    ("telo", "m"): "CCCTAA",
    ("seq", "M"): "regions.bed",
    ("comp", "r"): "regions.bed",
    ("seq", "X"): "60",
    ("seq", "Q"): "33",
    ("seq", "f"): "0.5",
    ("trimfq", "q"): "0.05",
    ("gc", "f"): "0.6",
    ("cutN", "n"): "5",
    ("sample", "s"): "11",
}

GENERIC = {"int": "2", "float": "0.5", "char": "N", "string": "N", "file": "names.txt"}

# Verified against the 1.5-r133 binary with the repository fixtures.
EXPECT_STDOUT = {
    "seq", "size", "comp", "sample", "subseq", "fqchk", "mergepe", "trimfq", "hety",
    "gc", "mutfa", "mergefa", "famask", "dropse", "rename", "randbase", "cutN", "gap",
    "listhet", "hpc", "hrun", "kfreq",
}
# split writes files instead of stdout; telo only prints BED once a telomere
# longer than the default -s 300 is found, which the fixtures do not reach.
MAY_STAY_SILENT = {"split", "telo"}

UNKNOWN_FLAG_WORDS = ("invalid option", "unknown option", "option requires an argument")


@unittest.skipUnless(BINARY, "no seqtk executable found (see docs/BUILD_SEQTK.md)")
class CommandsRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="seqtk-gui-test-")
        cls.cwd = cls.tmp.name
        (Path(cls.cwd) / "out").mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _run(self, argv: list[str]) -> subprocess.CompletedProcess:
        # errors="replace": seqtk speaks ASCII, but a localized Windows CRT can
        # inject GBK bytes into stderr, and a hard decode failure would leave
        # the stream as None instead of text the assertions can search.
        return subprocess.run([BINARY] + argv, capture_output=True, text=True,
                              errors="replace", cwd=self.cwd, timeout=60)

    def _positional_args(self, command: str) -> list[str]:
        out = []
        for item in POSITIONALS[command]:
            if item.startswith("tmp:"):
                out.append(str(Path(self.cwd) / item[4:]))
            elif (FIXTURES / item).is_file():
                out.append(str(FIXTURES / item))
            else:
                out.append(item)
        return out

    def test_every_command_exits_zero(self):
        self.assertEqual(sorted(c.name for c in COMMANDS), sorted(POSITIONALS))
        for name in sorted(POSITIONALS):
            with self.subTest(command=name):
                result = self._run([name] + self._positional_args(name))
                self.assertEqual(result.returncode, 0,
                                 f"{name}: stderr={result.stderr[:400]}")
                for word in UNKNOWN_FLAG_WORDS:
                    self.assertNotIn(word, result.stderr, f"{name} complained about arguments")
                if name in EXPECT_STDOUT:
                    self.assertTrue(result.stdout.strip(), f"{name} printed nothing")
                elif name not in MAY_STAY_SILENT:  # pragma: no cover - guard
                    self.fail(f"{name} is not classified")

    def test_split_writes_numbered_files(self):
        prefix = Path(self.cwd) / "three" / "part"
        prefix.parent.mkdir(parents=True, exist_ok=True)
        result = self._run(["split", "-n", "3", str(prefix), str(FIXTURES / "sample.fa")])
        self.assertEqual(result.returncode, 0, result.stderr[:300])
        written = sorted(prefix.parent.glob("part.*"))
        self.assertEqual(len(written), 3, f"expected 3 files, got {written}")
        self.assertTrue(any(path.stat().st_size for path in written))

    def test_telo_reports_counts_on_stderr_and_prints_with_a_lower_threshold(self):
        result = self._run(["telo"] + self._positional_args("telo"))
        self.assertEqual(result.returncode, 0)
        self.assertIn("\t", result.stderr, "telo should summarise bases on stderr")
        tuned = self._run(["telo", "-s", "2"] + self._positional_args("telo"))
        self.assertEqual(tuned.returncode, 0)
        self.assertTrue(tuned.stdout.strip(), "telo found no telomere in the fixture")

    def test_kfreq_rejects_a_non_acgt_kmer(self):
        # Upstream asserts on every k-mer character, so the GUI must validate too.
        result = self._run(["kfreq", "AX", str(FIXTURES / "sample.fa")])
        self.assertNotEqual(result.returncode, 0)

    def test_every_exposed_option_is_accepted(self):
        for command in COMMANDS:
            for option in command.options:
                with self.subTest(command=command.name, flag=option.flag):
                    argv = [command.name]
                    if option.is_flag:
                        argv.append("-" + option.flag)
                    else:
                        value = OPTION_VALUES.get((command.name, option.flag),
                                                  GENERIC[option.value_kind])
                        if (FIXTURES / value).is_file():
                            value = str(FIXTURES / value)
                        argv += ["-" + option.flag, value]
                    argv += self._positional_args(command.name)
                    result = self._run(argv)
                    for word in UNKNOWN_FLAG_WORDS:
                        self.assertNotIn(word, result.stderr, f"{argv} rejected by seqtk")
                    self.assertEqual(result.returncode, 0,
                                     f"{argv} failed: {result.stderr[:300]}")

    def test_binary_reports_the_documented_version(self):
        result = self._run([])
        self.assertIn("Version: 1.5-r133", result.stderr)

    def test_documented_but_unimplemented_trimfq_upper_q_is_rejected(self):
        # The GUI deliberately does not expose trimfq -Q; prove it really is
        # unusable so the decision recorded in spec.py stays justified.
        result = self._run(["trimfq", "-Q"] + self._positional_args("trimfq"))
        self.assertTrue(any(word in result.stderr for word in UNKNOWN_FLAG_WORDS)
                        or result.returncode != 0,
                        f"unexpectedly accepted: {result.stderr[:200]}")

    def test_seq_without_n_lowercases_and_n_zero_masks_with_the_digit(self):
        # stk_seq starts with mask_chr = 0 (NUL) and only substitutes mask_chr
        # when it is non-zero, otherwise it lowercases the base. The usage text
        # calls that "0 for lowercase [0]", which is why seq -n has no default:
        # a prefilled 0 would put the digit 0 into the sequence.
        self.assertIsNone(option_of("seq", "n").default)
        read = str(FIXTURES / "sample.fq")
        self.assertIn("ACGAAGTGcC", self._run(["seq", "-q", "20", read]).stdout)
        self.assertIn("ACGAAGTG0C", self._run(["seq", "-q", "20", "-n", "0", read]).stdout)
        self.assertIn("ACGAAGTGNC", self._run(["seq", "-q", "20", "-n", "N", read]).stdout)

    def test_seq_x_replaces_lowercases_only_when_n_is_in_effect(self):
        # (flag & 1024) && mask_chr > 0 guards option -x in stk_seq.
        fa = str(FIXTURES / "sample.fa")
        self.assertIn("ACGTacgt", self._run(["seq", "-x", fa]).stdout)
        converted = self._run(["seq", "-x", "-n", "N", fa]).stdout
        self.assertIn("ACGTNNNNNNNN", converted)
        self.assertNotIn("acgt", converted)

    def test_trimfq_L_default_is_the_inert_value_from_the_code(self):
        # fixed_len is initialised to -1 in stk_trimfq while its usage text
        # prints [0]; the code tests fixed_len > 0, so all three agree.
        self.assertEqual(option_of("trimfq", "L").default, -1)
        fq = str(FIXTURES / "sample.fq")
        plain = self._run(["trimfq", fq]).stdout
        self.assertTrue(plain)
        for value in ("-1", "0"):
            self.assertEqual(self._run(["trimfq", "-L", value, fq]).stdout, plain,
                             f"-L {value} should be inert")

    def test_mergefa_counters_go_to_stderr_and_the_rejection_names_the_wrong_flag(self):
        one, two = str(FIXTURES / "sample.fa"), str(FIXTURES / "sample2.fa")
        merged = self._run(["mergefa", one, two])
        self.assertEqual(merged.returncode, 0, merged.stderr[:200])
        self.assertTrue(merged.stdout.lstrip().startswith(">"))
        self.assertIn("(same,diff,hom-het,het-hom,het-het)", merged.stderr)
        rejected = self._run(["mergefa", "-m", "-i", one, two])
        self.assertNotEqual(rejected.returncode, 0)
        # The guard tests is_mask && is_intersect but blames '-h'; spec.py keeps
        # the discrepancy on record instead of copying the message.
        self.assertIn("`-i' and `-h'", rejected.stderr)
        self.assertIn("'-h'", COMMANDS_BY_NAME["mergefa"].notes_en)
        self.assertIn("-h", COMMANDS_BY_NAME["mergefa"].notes_zh)

    def test_telo_aborts_on_a_motif_character_that_is_not_acgt(self):
        # stk_telo asserts seq_nt6_table[motif[i]] is in 1..4, exactly like
        # stk_kfreq asserts its k-mer, so an invalid -m value is fatal.
        result = self._run(["telo", "-m", "XYZ", str(FIXTURES / "sample.fa")])
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
