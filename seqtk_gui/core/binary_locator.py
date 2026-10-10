"""Find and identify the seqtk executable the GUI should shell out to."""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .paths import bundled_binary_candidates

EXPECTED_VERSION = "1.5-r133"
_VERSION_RE = re.compile(r"Version:\s*(\S+)")


@dataclass(frozen=True)
class Candidate:
    path: Path
    source: str  # "setting" | "bundled" | "path"

    @property
    def exists(self) -> bool:
        return self.path.is_file()


def candidates(explicit: Optional[str] = None) -> list[Candidate]:
    """Ordered list of plausible seqtk locations, best first."""
    out: list[Candidate] = []
    if explicit:
        out.append(Candidate(Path(explicit), "setting"))
    for path in bundled_binary_candidates():
        out.append(Candidate(path, "bundled"))
    found = shutil.which("seqtk")
    if found:
        out.append(Candidate(Path(found), "path"))
    return out


def resolve(explicit: Optional[str] = None) -> Optional[Path]:
    for candidate in candidates(explicit):
        if candidate.exists:
            return candidate.path
    return None


def detect_version(binary: Path, timeout: float = 5.0) -> Optional[str]:
    """Read the version seqtk prints on stderr when called without arguments."""
    try:
        proc = subprocess.run([str(binary)], capture_output=True, timeout=timeout,
                              stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = (proc.stdout or b"") + (proc.stderr or b"")
    match = _VERSION_RE.search(text.decode("utf-8", errors="replace"))
    return match.group(1) if match else None
