#!/usr/bin/env python3
"""Entry point for `python main.py` (and for the PyInstaller spec)."""

from __future__ import annotations

import sys

from seqtk_gui.app import run

if __name__ == "__main__":
    sys.exit(run())
