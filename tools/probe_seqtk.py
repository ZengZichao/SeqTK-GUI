"""Probe a real seqtk executable against the GUI's command spec.

Maintenance helper: it runs every subcommand, and every single option of every
subcommand, against the test fixtures and reports the exit code and how much it
printed. Use it after an upstream seqtk release to see whether the spec in
seqtk_gui/core/spec.py still matches the binary.

    python tools/probe_seqtk.py [path/to/seqtk]
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from seqtk_gui.core.binary_locator import resolve  # noqa: E402
from seqtk_gui.core.spec import COMMANDS  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"
GENERIC = {"int": "2", "float": "0.5", "char": "N", "string": "N", "file": "regions.bed"}
# Values that would make a command divide by zero or write nothing on the small fixtures.
OVERRIDES = {
    ("hety", "w"): "10", ("hety", "t"): "2", ("split", "n"): "2",
    ("telo", "m"): "CCCTAA", ("seq", "M"): "regions.bed", ("comp", "r"): "regions.bed",
    ("seq", "X"): "60", ("seq", "Q"): "33", ("seq", "f"): "0.5",
    ("trimfq", "q"): "0.05", ("gc", "f"): "0.6", ("cutN", "n"): "5", ("sample", "s"): "11",
}
POSITIONALS = {
    "seq": ["sample.fa"], "size": ["sample.fa"], "comp": ["sample.fa"],
    "sample": ["sample.fa", "1"], "subseq": ["sample.fa", "names.txt"],
    "fqchk": ["sample.fq"], "mergepe": ["sample.fq", "sample2.fq"],
    "split": ["tmp:out/part", "sample.fa"], "trimfq": ["sample.fq"], "hety": ["sample.fa"],
    "gc": ["sample.fa"], "mutfa": ["sample.fa", "mutations.txt"],
    "mergefa": ["sample.fa", "sample2.fa"], "famask": ["sample.fa", "sample2.fa"],
    "dropse": ["sample.fq"], "rename": ["sample.fa", "ren"], "randbase": ["sample.fa"],
    "cutN": ["sample.fa"], "gap": ["sample.fa"], "listhet": ["sample.fa"],
    "hpc": ["sample.fa"], "telo": ["sample.fa"], "hrun": ["sample.fa", "3"],
    "kfreq": ["AC", "sample.fa"],
}


def main(argv: list[str]) -> int:
    binary = argv[1] if len(argv) > 1 else str(resolve() or "")
    if not binary:
        print("no seqtk binary found", file=sys.stderr)
        return 2
    print(f"# seqtk probe with {binary}\n")
    with tempfile.TemporaryDirectory(prefix="seqtk-probe-") as tmp:
        cwd = tmp
        (Path(cwd) / "out").mkdir()
        print(f"{'command':10s} {'args':34s} {'rc':>3s} {'stdout':>7s} {'stderr':>7s}  note")
        for command in COMMANDS:
            args = []
            for item in POSITIONALS[command.name]:
                if item.startswith("tmp:"):
                    args.append(str(Path(cwd) / item[4:]))
                elif (FIXTURES / item).is_file():
                    args.append(str(FIXTURES / item))
                else:
                    args.append(item)
            result = run(binary, [command.name] + args, cwd)
            print(f"{command.name:10s} {'(default)':34s} {result.returncode:3d} "
                  f"{len(result.stdout):7d} {len(result.stderr):7d}  {result.stderr.strip()[:60]}")
            for option in command.options:
                opts = ["-" + option.flag]
                if not option.is_flag:
                    value = OVERRIDES.get((command.name, option.flag),
                                          GENERIC[option.value_kind])
                    opts.append(str(FIXTURES / value) if (FIXTURES / value).exists() else value)
                single = run(binary, [command.name] + opts + args, cwd)
                verdict = "ok" if single.returncode == 0 and "option" not in single.stderr else "CHECK"
                print(f"{'':10s} {(' '.join(opts)):34s} {single.returncode:3d} "
                      f"{len(single.stdout):7d} {len(single.stderr):7d}  {verdict} "
                      f"{single.stderr.strip()[:50]}")
    return 0


def run(binary: str, args: list[str], cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run([binary] + args, capture_output=True, text=True, cwd=cwd, timeout=60)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
