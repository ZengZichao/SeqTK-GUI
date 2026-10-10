# Release checklist

Everything before the first `git push`. The repository is **not** initialised,
committed or pushed for you - the commands at the bottom are for you to run once
you have reviewed the tree.

## 1. Verify the code

```powershell
python -m pytest tests -q                     # all green, real-binary tests not skipped
python tools/probe_seqtk.py                   # every subcommand + every option, rc=0
python scripts/generate_commands_doc.py       # no diff afterwards
python main.py                                # launch it for real
tools\build_exe_windows.bat                   # build the single-file exe
dist\SeqTK-GUI.exe                            # launch the packaged build too
```

In the running app, check by hand:

* [ ] a real FASTA and a real FASTQ both open and convert
* [ ] `seq -A`, `sample`, `subseq`, `split` and `telo` each produce what you expect
* [ ] the **Command line** tab matches what you would have typed
* [ ] a bad path shows seqtk's `[E::…]` message in the log tab, not in the result tab
* [ ] **Write stdout to a file** produces a byte-identical file to the same command
      in a terminal with `>`
* [ ] **View > Language** and **View > Theme** change everything, including the form
* [ ] restart the app: language, theme, last command and form values are restored
* [ ] the status bar shows the seqtk path and `1.5-r133`

## 2. Verify the documentation

* [ ] `README.md` and `README.zh-CN.md` describe the same feature set
* [ ] every link in both READMEs resolves to a file in this tree
* [ ] `docs/` holds both languages for each page
* [ ] the unofficial statement appears in both READMEs, in the About dialog and in
      `LICENSE.txt`
* [ ] `LICENSE.txt` carries the project MIT text **and**, verbatim, seqtk's MIT
      notice plus the MIT notices of `kseq.h` and `khash.h` - the headers
      `seqtk.c` includes, so `bin/windows/seqtk.exe` is a copy of them too
* [ ] the upstream typo is still there: `grep -c "20082-2012" LICENSE.txt
      docs/THIRD_PARTY_NOTICES.md docs/THIRD_PARTY_NOTICES.zh-CN.md` must report a
      hit in all three - nobody has "helpfully" corrected it
* [ ] `bin/windows/LICENSE.seqtk.txt` is byte-identical to the upstream `LICENSE`
      (`cmp` it against the seqtk source tree), so the notice travels with the
      binary, as MIT requires for every copy
* [ ] nothing in `docs/THIRD_PARTY_NOTICES*.md` claims seqtk is *not* redistributed
      while `bin/windows/seqtk.exe` is present; the same claim must not appear in
      either README or in `LICENSE.txt`
* [ ] the project's own copyright line names a holder you are willing to publish.
      `Copyright (c) <year> SeqTK-GUI contributors` is the deliberate choice here:
      it satisfies MIT's "whoever the copyright holder is" requirement without
      exposing a real name or a personal e-mail address. Keep the upstream
      `Heng Li <lh3@me.com>` line - it is seqtk's notice, not yours, and MIT
      obliges you to reproduce it. If you would rather be named, use a stable
      public handle (the GitHub login) instead of an e-mail address, and update
      `LICENSE.txt`, `CONTRIBUTING*.md` and every `SPDX-License-Identifier` header
      in the same commit.
* [ ] screenshots match the current UI: `python scripts/make_screenshots.py`
* [ ] open all four images and read the path fields: they show the placeholder
      `C:\seqtk-demo\...` by design, never the folder you actually work in

## 3. Check nothing unwanted is tracked

```powershell
git init -b main
git add -A
git status --short            # review this list line by line
```

Expected: source, tests, fixtures, docs, screenshots, `LICENSE.txt`,
`README*.md`, `CONTRIBUTING*.md`, `requirements.txt`, `pyproject.toml`,
`.gitignore`, `.gitattributes`, `packaging/` (including `packaging/licenses/`),
`tools/`, `bin/windows/seqtk.exe`, `bin/windows/LICENSE.seqtk.txt` and
`dist/SeqTK-GUI.exe` (the packaged executable is tracked on purpose so the
repository itself ships a runnable program).

Must not appear: `__pycache__/`, `.pytest_cache/`, `build/`,
`*.ini` written under `docs/screenshots/`, any personal path, any input dataset.
`build/SeqTK-GUI/*.toc` records absolute paths on the machine that built it
(`D:\...`, `C:\Users\...`) - that is another reason `build/` stays ignored.

The published binary itself has to pass the same test, because a `-g` build
writes the directory it was compiled in into the executable. Replace `D` with
the drive your checkout lives on:

```bash
grep -a -o -F 'D:/' bin/windows/seqtk.exe | wc -l
grep -a -o -F 'D:\' bin/windows/seqtk.exe | wc -l
```

Both must print `0`. If either does not, rebuild `seqtk.exe` with
[docs/BUILD_SEQTK.md](BUILD_SEQTK.md) - whose command line forces `-g0` and the
`-ffile-prefix-map` rewrites and whose script refuses to finish on a binary that
names this machine - then update the checksum recorded there. Note that checking
only `C:\Users` is not enough: a checkout outside the profile directory leaks its
own drive path instead, and a non-ASCII directory name defeats byte-for-byte
matching, which is why the check is driven by the build path itself. Toolchain
paths such as the compiler's own build directory are not personal data and may
remain.

`bin/windows/seqtk.exe` is the one tracked file that can still carry a build
path, because the compiler writes it in. Check it from the project root:

```powershell
Select-String -Path bin\windows\seqtk.exe -Pattern (Get-Location).Path -SimpleMatch -Quiet
```

`False` is the answer you want. `True` means it was built with debug info turned
on - rebuild it with `tools\seqtk-build\build_seqtk_windows.bat`, which passes
`-g0` and the prefix maps, before publishing.

Decide deliberately about `bin/windows/seqtk.exe` (246 KB, tracked on purpose so
a clone runs out of the box). If you prefer not to commit binaries, delete it and
keep [docs/BUILD_SEQTK.md](BUILD_SEQTK.md) as the instructions - see its last
section. Whichever you pick, the licence documents in `packaging/licenses/` and
the bundled `LICENSE.seqtk.txt` are required only as long as the binary ships.

Also confirm your own identity before committing, since it is not configured
globally on this machine:

```powershell
git config user.name "Your Name"
git config user.email "you@example.com"
```

## 4. Commit and tag

```powershell
git commit -m "Add an unofficial PySide6 front end for seqtk 1.5-r133"
git tag -a v1.0.0 -m "First public release"
```

## 5. Publish (yours to run)

Create the repository on GitHub **without** initialising it, then:

```powershell
git remote add origin https://github.com/<owner>/seqtk-gui.git
git push -u origin main --follow-tags
```

Suggested repository settings once it exists:

* About: `Unofficial GUI front end for seqtk (PySide6). Not affiliated with seqtk.`
* Website: point at `README.md`
* License: GitHub will detect MIT from `LICENSE.txt`
* Branch protection on `main` if collaborators will push
* A `SECURITY.md` is unnecessary until someone asks for one; report issues by
  opening a private one on GitHub instead

## 6. After publishing

* Confirm the README renders on GitHub, including both screenshots and the
  bilingual documentation table.
* Run the suite once on a clean clone to catch anything `.gitignore` swallowed.
* Upload `dist/SeqTK-GUI.exe` (~48 MB) as a **Release** asset next to the tag -
  it is the one-file download for users with no Python. The same file is also
  tracked in the tree by design; after rebuilding it for a release, commit the
  fresh binary and attach it to the Release in the same push.
* Expect the first launch of the packaged exe to take a few seconds while
  PyInstaller unpacks to a temp folder, and consider Authenticode-signing it if
  your users hit SmartScreen or antivirus warnings.
