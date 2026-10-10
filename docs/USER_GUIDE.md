# User guide

1. [Before you start](#before-you-start)
2. [The window](#the-window)
3. [Choosing a subcommand](#choosing-a-subcommand)
4. [Filling the form](#filling-the-form)
5. [Running](#running)
6. [Reading results and errors](#reading-results-and-errors)
7. [Large outputs](#large-outputs)
8. [Language and theme](#language-and-theme)
9. [Per-command notes](#per-command-notes)
10. [Keyboard shortcuts](#keyboard-shortcuts)
11. [Troubleshooting](#troubleshooting)

## Before you start

If you downloaded the packaged **`SeqTK-GUI.exe`**, there is nothing to install:
the seqtk binary is inside it, and the first launch takes a few seconds while the
archive unpacks itself to a temporary folder.

The GUI needs a seqtk executable. It looks for one in this order and shows the
result in the status bar at the bottom right:

1. the path you saved under **Tools > Locate seqtk executable…**
2. the `bin/windows/seqtk.exe` that ships with the app - next to the source tree,
   or unpacked to a temporary folder when running the packaged build
3. `seqtk` found on `PATH`

The option list follows seqtk 1.5-r133. If your executable reports a different
version the status bar warns you; the run still works, but options may differ.

## The window

| Area | What it does |
| --- | --- |
| Left, top | Filter box; matches command names and the upstream help text |
| Left, list | All 24 subcommands, grouped as General / Regional analysis / Undocumented |
| Right, top | The parameter form for the selected subcommand: inputs, then options |
| Right, bottom | Tabs: **stdout**, **stderr / log**, **Command line**; **Clear output** and **Copy current tab** buttons sit beneath the tabs |
| Bottom bar | **Write stdout to a file** + path, **Run**, **Stop** |
| Status bar | Last run result (left), seqtk path and version (right) |

Drag the divider between the form and the output tabs to resize them. Drag a
FASTA/FASTQ file anywhere onto the window to fill the first file field.

## Choosing a subcommand

The grouping mirrors upstream's own usage output:

* **General** - `seq`, `size`, `comp`, `sample`, `subseq`, `fqchk`, `mergepe`,
  `split`, `trimfq`
* **Regional analysis** - `hety`, `gc`, `mutfa`, `mergefa`, `famask`, `dropse`,
  `rename`, `randbase`, `cutN`, `gap`, `listhet`, `hpc`, `telo`
* **Undocumented** - `hrun`, `kfreq`: dispatched by `main()` but absent from
  `seqtk`'s help text. They work the same way; the form labels them so you know
  where they came from.

Each form header repeats upstream's usage line, so you can compare it with
`seqtk <command>` in a terminal.

## Filling the form

**Inputs** are seqtk's positional arguments, in the order seqtk reads them.
Fields marked `*` are required. Use the `…` button to browse, or paste a path.
`split`'s prefix field picks a directory and appends the prefix name for you -
seqtk then writes `<prefix>.00001.fa`, `<prefix>.00002.fa`, and so on.

**Options** come in two shapes:

* a plain checkbox, e.g. `-r` - ticked means the flag is passed;
* a checkbox plus a value editor, e.g. `-l 60` - the value editor is only active
  while its checkbox is ticked.

Unticked options are **not** passed at all, so seqtk's own default applies. The
number shown next to a field is the upstream default; the value editor starts
there, but nothing reaches the command line until you tick the box. This keeps
the generated command line identical to what you would type yourself.

Numeric fields are bounded by what seqtk can use: `-Q` (quality shift) is capped
at 126, `-X` at 255, and so on. `-q`/`-f` accept decimals.

The **Command line** tab updates as you type. Copy it with
**Edit > Copy command line** to run or archive it in a terminal.

## Running

Press **Run** or Ctrl+R. The run is asynchronous: the window stays responsive,
output appears while seqtk works, and **Stop** kills the child process. When the
process exits, the status bar shows its exit code and elapsed seconds. A non-zero
exit switches to the log tab automatically.

seqtk's own messages (`[W::stk_seq] …`, `[E::stk_seq] failed to open the input
file/stream.`) land in the log tab, never in the result tab, so you can copy the
result tab without mixing in diagnostics.

## Reading results and errors

* **stdout** - the command's real output. For sequence commands this is FASTA or
  FASTQ text; for `size`, `comp`, `fqchk`, `gap`, `gc`, `telo`, `hrun`, `kfreq`
  it is a table.
* **stderr / log** - seqtk warnings and errors, plus GUI notes such as the output
  file size after a run.
* **Command line** - the exact invocation, quoted for your shell.

Some commands legitimately print nothing (`gap` with no gap long enough, `gc`
with no qualifying region, `telo` below its score threshold). An empty result tab
is not necessarily a failure - check the exit code in the status bar.

## Large outputs

The stdout tab is capped at 200,000 characters to keep the UI responsive; when a
run exceeds that, the tab says so and stops appending. For real work, tick
**Write stdout to a file** and give a path: the GUI then hands the file handle to
the child process, exactly like `>`, so gigabytes never enter memory. The tab
stays empty on purpose in that mode.

Overwriting an existing file asks for confirmation. `split` writes its own files
and ignores the stdout target - set a working directory (**File > Set working
directory…**) to control where they land.

## Language and theme

**View > Language** switches between 简体中文 and English immediately: menus, the
command list, form labels, hints, validation messages and the About dialog all
change without a restart. Option help text is a translation of upstream's own
wording; the flag letters and defaults stay untouched.

**View > Theme** switches between Light and Dark. Both are palettes plus a thin
stylesheet layer, so the app looks consistent on Windows and on the Qt styles
used elsewhere.

Your choice is remembered per user.

## Per-command notes

Worth knowing before the first run (full details in
[COMMANDS.md](COMMANDS.md)):

* `seq -A` and `seq -a` are the same flag upstream; the form exposes `-A`.
* `seq -n 0` means "mask to lowercase", not "mask to the digit zero".
* `seq -M` needs a BED or name list; combine with `-c` to mask the complement.
* `sample` on paired files needs the same `-s` seed twice to keep pairs aligned.
* `trimfq -b`, `-e` or `-L` disable `-q` and `-l` upstream; the form does not
  hide that, it is seqtk's own precedence.
* `trimfq -Q` appears in upstream's help text but its `getopt()` does not accept
  it, so the GUI does not offer it.
* `mergefa -m` and `-i` cannot be combined; seqtk exits with an error.
* `telo` writes BED to stdout and its `(telo_bases, input_bases)` summary to
  stderr; lower `-s` to detect short motifs.
* `kfreq` asserts that every k-mer character is A/C/G/T and aborts otherwise -
  the form validates the same rule before launching.

## Keyboard shortcuts

| Keys | Action |
| --- | --- |
| Ctrl+R | Run |
| Esc | Stop |
| Ctrl+O | Open input file |
| Ctrl+L | Clear output |
| Ctrl+Q | Quit |

## Troubleshooting

**Status bar says seqtk was not found.** Set the path with
**Tools > Locate seqtk executable…**, or put seqtk on `PATH`.

**Version mismatch warning in the status bar.** The bundled binary reports
1.5-r133. A different executable may accept fewer or more options; re-check the
usage text of your own build.

**The result tab is empty but the exit code is 0.** Normal for commands that
found nothing, and for `split`, which writes files instead of stdout.

**Output stops mid-run.** You hit the 200,000-character preview cap; tick
**Write stdout to a file**.

**Gibberish characters in the log.** seqtk prints plain ASCII; anything unreadable
comes from your input file, not from the GUI's decoding (UTF-8 with replacement).

**Chinese text shows as boxes on a server without CJK fonts.** Switch to English
under **View > Language**, or install a CJK font.
