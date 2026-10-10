# Development

## Architecture

```
main.py
  -> seqtk_gui/app.py            QApplication, settings, language, theme
       -> ui/main_window.py      wires everything together
            ui/command_list.py   24 subcommands, grouped + filterable
            ui/param_panel.py    form generated from core/spec.py
            ui/output_panel.py   stdout / stderr / command line tabs
            ui/themes.py         light + dark palette and stylesheet
            ui/about_dialog.py   unofficial notice, license text
                 |
                 v
            core/cli_build.py    spec + form values -> argv, validation
            core/runner.py       QProcess: streaming, optional stdout->file
            core/binary_locator.py  find seqtk, read its reported version
            core/paths.py        per-platform layout
            core/settings.py     persisted preferences
            i18n/catalog.py      JSON catalogs, runtime language switch
```

The dependency direction is strict: `core` imports no Qt widgets (only
`QtCore`), `i18n` imports no `ui`, and `ui` is the only layer that touches
widgets. `core/spec.py` imports nothing but the standard library, which is why
the tests and the documentation generator can consume it without a display.

## The one rule that matters

`seqtk_gui/core/spec.py` is a transcription of `seqtk.c`, not a design document.
Every option, value type and default must come from the upstream source:

* the option set from the `getopt(argc, argv, "...")` call of the matching
  `stk_*` function;
* whether an option takes a value from the `:` after its letter;
* defaults from the variable initialisations at the top of that function;
* positional order from how the function indexes `argv[optind]`.

`tests/test_spec_against_source.py` re-checks the option sets against a copy of
those getopt strings, and `tests/test_seqtk_execution.py` runs every option
against a real binary. When upstream adds or removes a flag, both fail.

### Changing or adding an option

1. Read the relevant `stk_*` function in `seqtk.c`.
2. Edit `spec.py` - the `Option`/`Positional` entries, keeping bilingual help.
3. `python scripts/generate_commands_doc.py` (the command tables are generated;
   `tests/test_docs_are_generated.py` fails if you skip this).
4. `python -m pytest tests -q`, then `python tools/probe_seqtk.py` if a binary
   is available.

## Form value semantics

A valued option is stored as `None` when its checkbox is off, and as a typed
value when on. `cli_build.build_argv` skips `None` entirely, so the GUI never
sends a flag the user did not ask for and seqtk's own defaults stay authoritative.
Positional values are plain strings, in spec order.

Per-command form state is persisted as `form/<command>/<key>` strings, where a
valued option is encoded `"enabled|value"`. See `SettingsStore.save_form`.

## Output handling

`SeqtkRunner` uses `QProcess` with separate channels and emits decoded chunks.
Two modes:

* preview - chunks go to the stdout tab, capped by `MAX_PREVIEW_CHARS`;
* redirect - `setStandardOutputFile()` hands the child a file handle, so the data
  never passes through Python. This is the GUI equivalent of `>`.

Decoding is UTF-8 with `errors="replace"`; seqtk writes ASCII, and this keeps a
stray byte from killing the read.

## Internationalisation

`i18n/strings/strings_zh.json` and `strings_en.json` hold every UI string. Keys
are dotted and grouped by surface (`menu.`, `act.`, `panel.`, `field.`,
`status.`, `validate.`, `dialog.`, `run.`, `output.`, `tab.`, `about.`, `usage.`,
`theme.`, `msg.`).

* Add a key to **both** files; `tests/test_i18n_completeness.py` compares the key
  sets, rejects empty values, checks `{placeholder}` parity, and scans the source
  for `tr("…")` calls whose key is missing.
* `Language.pick(en, zh)` is for text that lives in the spec data rather than a
  catalog - upstream help wording and its translation.
* Widgets that must follow a language change register a provider callable in
  `ParamPanel._retranslate` and get replayed by `retranslate()`.

## Themes

`ui/themes.py` exposes `light` and `dark` as a colour dict, a `QPalette` builder
and a stylesheet. `apply_theme()` also pins the Fusion style so both platforms
render the palette consistently. Add a colour to the dict, never to a literal in
a widget.

## Testing

```bash
python -m pytest tests -q                        # everything
python -m pytest tests -q --ignore=tests/test_seqtk_execution.py   # no binary needed
python tools/probe_seqtk.py [path\to\seqtk.exe]  # manual sweep of all options
```

Notes:

* UI tests run with `QT_QPA_PLATFORM=offscreen` and a throwaway `QSettings` file,
  so they never touch real preferences.
* Modal dialogs are stubbed in `tests/conftest.py`; a real `QMessageBox` would
  block an offscreen run forever.
* After starting a process from a test, pump the event loop with
  `wait_for(app, predicate)` - a bare `processEvents()` loop returns instantly and
  the child is never reaped.
* Real-binary tests skip themselves when no seqtk executable is found.

## Packaging

```powershell
tools\build_exe_windows.bat
```

installs PyInstaller when missing and runs `packaging/SeqTK-GUI.spec`, producing
**one self-contained `dist/SeqTK-GUI.exe`**. The spec packs two things as data:

* `seqtk_gui/i18n/strings/*.json` - the UI catalogs;
* `bin/<platform>/seqtk[.exe]` - the native binary the app executes.

At startup PyInstaller unpacks both into `sys._MEIPASS`, and
`core/paths.py::bundled_binary_candidates()` lists that directory before the
executable's own folder, so the app finds its bundled seqtk with no user setup.
`tests/test_binary_lookup.py` pins that lookup order, including the frozen case.

Set `ONEFILE=0` to build a folder distribution instead - it starts faster and is
easier for antivirus tools to accept, at the cost of shipping many files.

To check a build without a test harness: launch `dist/SeqTK-GUI.exe`, confirm the
window title reads `SeqTK-GUI (…) - seqtk 1.5-r133`, and look for
`%TEMP%\_MEI*\bin\windows\seqtk.exe` while it runs - that is the bundled copy in
use. The status bar shows the resolved path.

On macOS, build the same way and wrap the result in a `.app`, keeping the seqtk
binary inside `Contents/MacOS` or `Contents/Resources` so the resolver still
finds it.

## Porting to another OS

Nothing in the app is Windows-specific. To add a platform:

1. `core/paths.py` - map `sys.platform` in `PLATFORM_DIRS`, and add the config
   directory branch.
2. `core/binary_locator.py` - `executable_name()` already returns `seqtk` off
   Windows.
3. `tools/seqtk-build/` - add a build script; the MinGW PRNG shim is Windows-only.
4. Drop the binary in `bin/<platform>/` and run the suite: the real-execution
   tests pick it up through the same resolver.

## Conventions

* Comments describe present design and constraints only - no history, no
  "previously", no task references.
* No dead constants, unused styles or unreachable branches; the repo is published
  as-is.
* Content labels stay left-aligned; status, hint and empty-state text is centred.
* Text on an accent-coloured background is always white.
* seqtk's help wording is quoted, not paraphrased, so users can grep upstream.
