"""Turn a spec ``Command`` plus form values into a seqtk argument vector."""

from __future__ import annotations

import math
import re
import shlex
import sys
from typing import Any, Mapping, Optional

from .spec import KIND_KMER, KIND_NUMBER, Command, Option

OPT_PREFIX = "opt:"
POS_PREFIX = "pos:"

KMER_RE = "ACGTacgt"

# seqtk parses numbers with atoi/atof, which stop at the first character they
# cannot read: "1_000" becomes 1 and "nan"/"inf" become 0, all with exit code 0.
# Only a strictly decimal, finite literal may reach the process. The digit class
# is ASCII by hand - \d would let "５" through, which float() reads as 5 while
# atof reads as 0.
_DECIMAL_RE = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")

# stk_sample counts records through ``(uint64_t)(frac + .499)``, so a finite
# value at or above 2**64 wraps to 0: seqtk then writes nothing, exits 0 and
# reports no error at all.
_UINT64_LIMIT = 2.0 ** 64


def _is_decimal(text: str) -> bool:
    if _DECIMAL_RE.match(text) is None:
        return False
    try:
        number = float(text)
    except ValueError:
        return False
    return math.isfinite(number) and abs(number) < _UINT64_LIMIT


def opt_key(flag: str) -> str:
    return OPT_PREFIX + flag


def pos_key(name: str) -> str:
    return POS_PREFIX + name


def _as_cli_value(option: Option, value: Any) -> str:
    if option.value_kind == "int":
        return str(int(value))
    if option.value_kind == "float":
        text = repr(float(value))
        return text
    if option.value_kind == "char":
        return str(value)[0]
    return str(value)


def validate(cmd: Command, values: Mapping[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Return the list of problems as (message-id, kwargs) pairs."""
    problems: list[tuple[str, dict[str, Any]]] = []

    for positional in cmd.positionals:
        raw = values.get(pos_key(positional.key))
        text = "" if raw is None else str(raw).strip()
        if not text:
            if positional.required:
                problems.append(("validate.required", {"field": positional.key}))
            continue
        if text.startswith("-"):
            # seqtk parses options out of order, so a positional that begins with
            # '-' becomes an option instead of a file (``seq -l100`` swallows the
            # file argument and then waits for stdin forever). A lone '-' also
            # means stdin, which the GUI never feeds. Upstream cannot be saved
            # with a '--' terminator: half of the stk_* handlers read argv[1]
            # directly, so the value has to be rejected here.
            problems.append(("validate.dash", {"field": positional.key}))
            continue
        if positional.kind == KIND_NUMBER:
            if not _is_decimal(text):
                problems.append(("validate.number", {"field": positional.key}))
        elif positional.kind == KIND_KMER:
            bad = sorted({ch for ch in text if ch not in KMER_RE})
            if not text:
                problems.append(("validate.required", {"field": positional.key}))
            elif bad:
                problems.append(("validate.kmer", {"field": positional.key,
                                                   "chars": "".join(bad)}))

    for option in cmd.valued:
        raw = values.get(opt_key(option.flag))
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            continue
        if option.value_kind in ("int", "float"):
            if not _is_decimal(str(raw)):
                problems.append(("validate.opt_number", {"flag": option.flag}))
                continue
            number = float(raw)
            if option.min_value is not None and number < option.min_value:
                problems.append(("validate.opt_range", {"flag": option.flag,
                                                         "lo": option.min_value,
                                                         "hi": option.max_value}))
            elif option.max_value is not None and number > option.max_value:
                problems.append(("validate.opt_range", {"flag": option.flag,
                                                         "lo": option.min_value,
                                                         "hi": option.max_value}))
    return problems


def build_argv(cmd: Command, values: Mapping[str, Any]) -> list[str]:
    """Build the arguments after the subcommand name, in seqtk's own order."""
    argv: list[str] = [cmd.name]

    for option in cmd.options:
        raw = values.get(opt_key(option.flag))
        if raw is None or raw is False or raw == "":
            continue
        if option.is_flag:
            if raw is True:
                argv.append("-" + option.flag)
            continue
        argv.extend(["-" + option.flag, _as_cli_value(option, raw)])

    for positional in cmd.positionals:
        raw = values.get(pos_key(positional.key))
        text = "" if raw is None else str(raw).strip()
        if text:
            argv.append(text)

    return argv


def build_command_line(cmd: Command, values: Mapping[str, Any], binary: Optional[str] = None) -> str:
    """A copy-friendly display form, quoted for the running platform."""
    argv = ([binary] if binary else ["seqtk"]) + build_argv(cmd, values)
    if sys.platform == "win32":
        return " ".join(_quote_win(part) for part in argv)
    return " ".join(shlex.quote(part) for part in argv)


def _quote_win(text: str) -> str:
    if text and all(ch not in text for ch in ' "\t&<>|^'):
        return text
    # Quoting follows CommandLineToArgvW: a run of N backslashes is literal
    # unless it sits just before a quote, where 2N+1 emit N plus an escaped
    # '"' and 2N emit N plus a quote that ends the argument. Trailing
    # backslashes therefore have to be doubled, or "C:\dir\" would swallow the
    # closing quote and merge the next argument into this one.
    parts = ['"']
    slashes = 0
    for ch in text:
        if ch == "\\":
            slashes += 1
            continue
        if ch == '"':
            parts.append("\\" * (slashes * 2 + 1) + '"')
        else:
            parts.append("\\" * slashes + ch)
        slashes = 0
    parts.append("\\" * (slashes * 2) + '"')
    return "".join(parts)
