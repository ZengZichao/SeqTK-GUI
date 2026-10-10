"""Argument vector construction and validation."""

from __future__ import annotations

import unittest

from seqtk_gui.core import cli_build
from seqtk_gui.core.spec import COMMANDS, get_command


class BuildArgv(unittest.TestCase):
    def test_flags_and_values_keep_declaration_order(self):
        cmd = get_command("seq")
        argv = cli_build.build_argv(cmd, {
            cli_build.opt_key("A"): True,
            cli_build.opt_key("l"): 60,
            cli_build.opt_key("r"): True,
            cli_build.pos_key("input"): "in.fq",
        })
        self.assertEqual(argv, ["seq", "-l", "60", "-r", "-A", "in.fq"])

    def test_disabled_valued_option_is_omitted(self):
        cmd = get_command("seq")
        argv = cli_build.build_argv(cmd, {cli_build.opt_key("q"): None,
                                          cli_build.pos_key("input"): "in.fa"})
        self.assertEqual(argv, ["seq", "in.fa"])

    def test_int_value_is_not_written_as_float(self):
        argv = cli_build.build_argv(get_command("gap"),
                                    {cli_build.opt_key("l"): 50, cli_build.pos_key("input"): "a.fa"})
        self.assertEqual(argv, ["gap", "-l", "50", "a.fa"])

    def test_float_value_keeps_precision(self):
        argv = cli_build.build_argv(get_command("trimfq"),
                                    {cli_build.opt_key("q"): 0.05, cli_build.pos_key("input"): "a.fq"})
        self.assertEqual(argv, ["trimfq", "-q", "0.05", "a.fq"])

    def test_positionals_follow_spec_order(self):
        argv = cli_build.build_argv(get_command("split"),
                                    {cli_build.pos_key("prefix"): "out/part",
                                     cli_build.pos_key("input"): "in.fa",
                                     cli_build.opt_key("n"): 3})
        self.assertEqual(argv, ["split", "-n", "3", "out/part", "in.fa"])

        argv = cli_build.build_argv(get_command("sample"),
                                    {cli_build.pos_key("input"): "in.fa",
                                     cli_build.pos_key("number"): "100"})
        self.assertEqual(argv, ["sample", "in.fa", "100"])

        argv = cli_build.build_argv(get_command("kfreq"),
                                    {cli_build.pos_key("kmer"): "ACGT",
                                     cli_build.pos_key("input"): "in.fa"})
        self.assertEqual(argv, ["kfreq", "ACGT", "in.fa"])

    def test_char_option_sends_one_character(self):
        argv = cli_build.build_argv(get_command("seq"),
                                    {cli_build.opt_key("n"): "NNN",
                                     cli_build.pos_key("input"): "in.fa"})
        self.assertEqual(argv, ["seq", "-n", "N", "in.fa"])

    def test_display_line_quotes_paths_with_spaces(self):
        cmd = get_command("seq")
        text = cli_build.build_command_line(cmd, {cli_build.pos_key("input"): "C:/tmp/my file.fa"},
                                            binary="seqtk")
        self.assertIn('"C:/tmp/my file.fa"', text.replace("\\", "/") if '"' in text else text)

    def test_every_command_is_buildable_from_defaults(self):
        for cmd in COMMANDS:
            values = {}
            for option in cmd.options:
                values[cli_build.opt_key(option.flag)] = True if option.is_flag else None
            for positional in cmd.positionals:
                values[cli_build.pos_key(positional.key)] = "x" if positional.required else ""
            argv = cli_build.build_argv(cmd, values)
            self.assertEqual(argv[0], cmd.name)
            self.assertGreaterEqual(len(argv), 2)


class Validation(unittest.TestCase):
    def test_missing_required_positional(self):
        problems = cli_build.validate(get_command("seq"), {})
        keys = [key for key, _ in problems]
        self.assertEqual(keys, ["validate.required"])

    def test_optional_positional_may_be_empty(self):
        problems = cli_build.validate(get_command("rename"),
                                      {cli_build.pos_key("input"): "a.fq"})
        self.assertEqual(problems, [])

    def test_number_positional_must_be_numeric(self):
        problems = cli_build.validate(get_command("sample"),
                                      {cli_build.pos_key("input"): "a.fa",
                                       cli_build.pos_key("number"): "many"})
        self.assertIn("validate.number", [key for key, _ in problems])

    def test_kmer_rejects_non_acgt(self):
        problems = cli_build.validate(get_command("kfreq"),
                                      {cli_build.pos_key("kmer"): "ACXZ",
                                       cli_build.pos_key("input"): "a.fa"})
        self.assertEqual(len(problems), 1)
        key, kwargs = problems[0]
        self.assertEqual(key, "validate.kmer")
        self.assertEqual(kwargs["chars"], "XZ")

    def test_option_range_is_enforced(self):
        problems = cli_build.validate(get_command("seq"),
                                      {cli_build.opt_key("Q"): 200,
                                       cli_build.pos_key("input"): "a.fa"})
        self.assertIn("validate.opt_range", [key for key, _ in problems])

    def test_positional_starting_with_dash_is_rejected(self):
        # seqtk's getopt permutes, so a positional that starts with '-' turns
        # back into an option: the file argument disappears and seqtk then blocks
        # reading a stdin the GUI never closes.
        for value in ("-h", "--help", "-", "-l100", "-r", " -x"):
            with self.subTest(value=value):
                problems = cli_build.validate(get_command("seq"),
                                              {cli_build.pos_key("input"): value})
                self.assertEqual([key for key, _ in problems], ["validate.dash"])

    def test_dash_rule_covers_every_positional_of_a_two_file_command(self):
        cmd = get_command("subseq")
        problems = cli_build.validate(cmd, {cli_build.pos_key("input"): "-t",
                                            cli_build.pos_key("region"): "-M other.bed"})
        self.assertEqual([key for key, _ in problems], ["validate.dash", "validate.dash"])

    def test_dash_rule_also_blocks_the_kmer_and_number_fields(self):
        self.assertEqual([key for key, _ in cli_build.validate(
            get_command("kfreq"), {cli_build.pos_key("kmer"): "-A",
                                   cli_build.pos_key("input"): "a.fa"})], ["validate.dash"])
        self.assertIn("validate.dash", [key for key, _ in cli_build.validate(
            get_command("sample"), {cli_build.pos_key("input"): "a.fa",
                                    cli_build.pos_key("number"): "-1"})])

    def test_ordinary_paths_are_not_flagged_by_the_dash_rule(self):
        for value in ("a.fa", "C:/data/-weird-.fa", "/tmp/-x.fa", "..dir/file.fa",
                      "D:/x -y.fa"):
            with self.subTest(value=value):
                problems = cli_build.validate(get_command("seq"),
                                              {cli_build.pos_key("input"): value})
                self.assertEqual(problems, [])

    def test_valid_input_produces_no_problem(self):
        problems = cli_build.validate(get_command("seq"),
                                      {cli_build.opt_key("q"): 20, cli_build.opt_key("A"): True,
                                       cli_build.pos_key("input"): "a.fq"})
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
