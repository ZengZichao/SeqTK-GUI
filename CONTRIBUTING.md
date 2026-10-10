# Contributing

Thanks for taking an interest. This is an unofficial front end, so the bar for a
good contribution is: **stay faithful to seqtk, and keep both languages and both
themes in sync.**

## Ground rules

1. **seqtk does the work.** Never implement sequence parsing, conversion or
   counting in Python. If something is missing, it belongs upstream.
2. **The spec is a transcription.** Options, value types and defaults in
   `seqtk_gui/core/spec.py` must come from `seqtk.c` of the release you are
   targeting - see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md#the-one-rule-that-matters).
   Do not add flags that upstream's `getopt()` does not accept, even if a help
   text mentions them; record the mismatch in the command's `notes_*` instead.
3. **Bilingual or it does not merge.** Every user-visible string needs a Chinese
   and an English entry, and every documentation page needs both languages.
4. **No history in the tree.** Comments, docs and commit-facing text describe the
   current design only - no "previously", no changelog files, no issue numbers.
5. **MIT in, MIT out.** Submitting implies you agree your contribution is offered
   under the project's license.
6. **Licensing is declared once, at the root.** The repository does **not** carry
   a per-file SPDX or copyright header: `LICENSE.txt` governs every file, and
   stamping 30 identical headers would be noise that goes stale on the first
   rename. Two files are the deliberate exception, because a root `LICENSE.txt`
   does not reach them the way it reaches the Python package - `bin/windows/seqtk.exe`
   travels alone, and `tools/seqtk-build/mingw_prng_shim.c` is compiled outside
   the Python package and can be copied into somebody else's build without the
   repository around. Those two places are where an identifier actually adds
   information, so they carry one; leave the rest alone unless you are adding a
   file that will escape the tree the same way.
   The project's own copyright line is `Copyright (c) <year> SeqTK-GUI
   contributors`. That wording is intentional: MIT needs a copyright holder, and
   a collective designation satisfies that without publishing a real name or a
   personal e-mail address in a file that every downstream copy must reproduce.
   The upstream `Heng Li <lh3@me.com>` line is different - it is seqtk's notice
   that MIT obliges us to keep verbatim, and it must not be "cleaned up",
   anonymised or corrected, typo included.

## Setup

```bash
git clone <your fork>
cd seqtk-gui
python -m venv .venv
.venv\Scripts\activate          # Windows   (macOS/Linux: source .venv/bin/activate)
python -m pip install -r requirements.txt
python main.py
```

A seqtk executable is optional for most work; the tests that need one skip
themselves. Build it with [docs/BUILD_SEQTK.md](docs/BUILD_SEQTK.md) if you want
the full suite to run.

## Workflow

1. Branch from `main`.
2. Make the change.
3. If the spec changed: `python scripts/generate_commands_doc.py`.
4. If UI strings changed: update **both** `seqtk_gui/i18n/strings/*.json`.
5. Run the tests: `python -m pytest tests -q`.
6. Run the app once by hand and check the affected screen in both languages and
   both themes - type checking cannot catch a clipped layout.
7. Open a pull request that says what user-visible behaviour changed, and paste a
   screenshot when the UI moved.

## Where to start

* A translation or wording fix in `strings_zh.json` / `strings_en.json`.
* A missing example in [docs/USER_GUIDE.md](docs/USER_GUIDE.md).
* A platform gap in `core/paths.py` (macOS support is designed for, not built).
* A real bug: start with `python tools/probe_seqtk.py`, which sweeps every
  subcommand and option against your binary.

## Reporting problems

Include: seqtk version as shown in the status bar, the exact command line from the
**Command line** tab, the log tab contents, your OS, and how the input file looks
(a few records are enough - do not upload real data).

## Style

Python 3.10+, 4-space indent, roughly 100 columns, type hints on public
functions. Widgets are built in code, not in `.ui` files, so the form can be
generated from the spec. No new dependency without a reason that cannot be met by
the standard library.
