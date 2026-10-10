# Building the seqtk executable

The GUI never parses or converts sequences itself, so it needs a native seqtk
binary. This project ships `bin/windows/seqtk.exe`, compiled from unmodified
upstream `seqtk.c` (1.5-r133). Nothing in `seqtk-1.5/` is edited to produce it;
the only added file is a small compatibility shim kept here.

## Windows

Requirements: a MinGW-w64 gcc with zlib available (Strawberry Perl's toolchain
works, as does MSYS2's `mingw-w64-ucrt-x86_64-gcc` plus
`mingw-w64-ucrt-x86_64-zlib`).

For reference, the committed `bin/windows/seqtk.exe` carries two compiler
identifiers, and attributing them correctly matters when someone tries to
reproduce it: `GCC: (x86_64-posix-seh, Built by strawberryperl.com project)
8.3.0` is the compiler that built `seqtk.c` and the shim, while
`GCC: (x86_64-posix-seh-rev1, Built by MinGW-W64 project) 7.2.0` comes from the
prebuilt MinGW-W64 runtime objects that were linked in - it does not mean the
toolchain is 7.2.0. zlib 1.2.11 is linked statically. Any equivalent toolchain
builds a working binary; only the checksum below is tied to that exact one.

This recipe was re-run and produced a binary of the same size that behaved
**identically** to the shipped one across every subcommand and option covered by
`python tools\probe_seqtk.py`, while having a different SHA-256 - object
ordering and embedded paths change between runs. That is the practical meaning
of "reproducible" here: verifiable behaviour, not identical bytes.

```powershell
tools\seqtk-build\build_seqtk_windows.bat C:\path\to\seqtk-1.5
```

which runs the equivalent of:

```powershell
gcc -g0 -O2 -Wall -Wno-unused-function -Wno-format ^
    -ffile-prefix-map=<seqtk-src>=seqtk-1.5 ^
    -ffile-prefix-map=<repo>\tools\seqtk-build=tools/seqtk-build ^
    <seqtk-src>\seqtk.c tools\seqtk-build\mingw_prng_shim.c ^
    -o bin\windows\seqtk.exe -lz -lm
```

`-g0` and the two prefix maps are not optional. The binary is published, and a
plain `-g` build records the absolute directory it was compiled in - your user
folder would ship inside `seqtk.exe`. `assert()` also keeps `__FILE__` even with
no debug info, which is what the prefix maps rewrite. The build script fails if
the finished binary still contains the source path or your profile directory.

### Why the shim exists

`seqtk.c` calls `drand48()`, `srand48()` and `lrand48()` in `stk_randbase` and
`stk_mergefa`. The MSVC/MinGW C runtime does not provide them, so linking fails
with `undefined reference to 'drand48'`.
`tools/seqtk-build/mingw_prng_shim.c` implements the 48-bit linear congruential
generator from the Single UNIX Specification instead of stubbing it out, so
`randbase` and `mergefa -r` keep working on Windows. The shim is appended to the
compile line only - upstream source is untouched.

If your toolchain already provides those symbols (MSYS2 UCRT builds sometimes
do), drop the shim from the command line.

## macOS and Linux

No shim is needed; the POSIX runtime already has the drand48 family.

```bash
tools/seqtk-build/build_seqtk_macos.sh /path/to/seqtk-1.5     # -> bin/macos/seqtk
```

or by hand:

```bash
cc -O2 -Wall seqtk.c -o ../bin/macos/seqtk -lz
```

On a mac, install zlib with `brew install zlib` and point the compiler at it if
the linker cannot find it.

## Verify a build

The committed binary is identified so a rebuild can be compared against it:

```powershell
sha256sum bin\windows\seqtk.exe
# b844d8f0cee53681903f71848207d8ddace051d6aee51e79d1a49431bfe9846d
bin\windows\seqtk.exe                     # prints "Version: 1.5-r133" on stderr
bin\windows\seqtk.exe seq -A tests\fixtures\sample.fq
bin\windows\seqtk.exe randbase tests\fixtures\sample.fa   # exercises the shim
python tools\probe_seqtk.py                # every subcommand and option, at once
```

Rebuilds are not expected to reproduce those bytes exactly - the compiler
version, its build configuration and the zlib build all change the result - so
treat the checksum as an integrity check on the file you are running, and the
steps above as the way to confirm a rebuild behaves identically. The shipped
`.exe` links zlib **statically**, which is why
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) carries the zlib notice.

**Release gate on the committed checksum.** A published binary must not carry
the directory it was compiled in, so the committed `bin/windows/seqtk.exe` is
built by `tools\seqtk-build\build_seqtk_windows.bat`, which forces `-g0` and both
`-ffile-prefix-map` rewrites and refuses to finish on a binary that still names
the machine it was built on. The requirement is checked by counting the drive
prefix of the checkout: both counts below must be `0`. Replace `D` with the
drive your checkout lives on:

```bash
grep -a -o -F 'D:/' bin/windows/seqtk.exe | wc -l
grep -a -o -F 'D:\' bin/windows/seqtk.exe | wc -l
```

Both must print `0`. If either does not, rebuild with
`tools\seqtk-build\build_seqtk_windows.bat` - which forces `-g0` and the prefix
maps for exactly this reason - then write the new checksum here and in the
Chinese copy. Re-audit whenever the binary changes. The committed file meets the
gate: it is 246,433 bytes, both counts are `0`, and `tools/probe_seqtk.py` runs
all 82 subcommand/option probes against it. A rebuild does not byte-match it, so
the checksum identifies the artifact, while the probe run is what proves a
rebuild is still the same program.

`python -m pytest tests -q` picks the binary up automatically and skips the
real-execution tests when it is missing.

## License position

seqtk is MIT-licensed by its author. The compiled `seqtk.exe` is a copy of
seqtk, and MIT requires the copyright notice and the permission notice to be
kept in *all copies of the software* - a binary counts as a copy. That is why
`bin/windows/LICENSE.seqtk.txt` sits next to the `.exe`: it is a byte-identical
copy of the upstream `LICENSE` file, so the notice travels with the binary
itself and not only with the repository. The same text is reproduced in
[LICENSE.txt](../LICENSE.txt) here, and the packaging step bundles all of it
into `dist/SeqTK-GUI.exe`.

`seqtk.c` in turn includes `kseq.h` and `khash.h`, both MIT-licensed by
Attractive Chaos and both named by the upstream `Makefile` as prerequisites of
the `seqtk` target (`seqtk:seqtk.c khash.h kseq.h`), so they are compiled into
the shipped binary as part of it. Their notices are reproduced verbatim right
next to seqtk's in [LICENSE.txt](../LICENSE.txt) and are set out in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md); each header keeps its own
wording, which differs between the two.

Because the build adds `mingw_prng_shim.c`, the shipped binary is a **modified
version** of seqtk. MIT imposes no marking obligation, but zlib does ask that
altered versions not be misrepresented, and honesty about a binary nobody can
read is worth the two sentences, so the change is recorded above and in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The shim itself is original to
this project and carries its own `SPDX-License-Identifier: MIT` header; it is
not upstream code and does not put this file under Heng Li's copyright.

Nothing here is an official seqtk release, and the seqtk name is used only to
say what this front end drives - see the disclaimer in
[README.md](../README.md).

If you would rather not carry a prebuilt binary in git, delete
`bin/windows/seqtk.exe` (and `bin/windows/LICENSE.seqtk.txt`), point users at
this document, and have them place their own build there or select it via
**Tools > Locate seqtk executable…**.
