# Third-party notices

SeqTK-GUI is MIT-licensed (see [LICENSE.txt](../LICENSE.txt)). It is a separate,
**unofficial** work that drives other programs; the components below stay under
their own terms and are listed here so those terms travel with the repository
and with the packaged application.

Two distribution forms exist and their obligations differ, so each entry says
which form it affects:

* **Source form** - what you get from `git clone` (Python + docs +
  `bin/windows/seqtk.exe`).
* **Packaged form** - `dist/SeqTK-GUI.exe`, a PyInstaller *onefile* build that
  embeds the CPython runtime, PySide6 and the Qt 6 DLLs, plus `bin/windows/
  seqtk.exe`. Building and publishing it is where the LGPL obligations bite.

## seqtk

* Project: <https://github.com/lh3/seqtk>
* Author: Heng Li
* Version this project follows: **1.5-r133**
* License: MIT
* What is used, in both forms:
  * `seqtk_gui/core/spec.py` and [COMMANDS.md](COMMANDS.md) transcribe seqtk's
    `getopt()` option strings, defaults and usage text - a derivative work of
    seqtk, therefore still seqtk's MIT, not this project's.
  * `bin/windows/seqtk.exe` is a **copy of seqtk in binary form**: it is
    compiled from unmodified upstream `seqtk.c` plus one local compatibility
    file, `tools/seqtk-build/mingw_prng_shim.c` (see
    [BUILD_SEQTK.md](BUILD_SEQTK.md)). That makes it a modified version of
    seqtk, so this document marks the change explicitly, as MIT's derivative
    terms and zlib's clauses both ask for. seqtk is never linked into the
    Python process and is never relicensed here.
* Obligations carried: MIT requires the copyright notice and the permission
  notice to be included in *all copies or substantial portions* of the software.
  A binary is such a copy, so the verbatim notice is placed where the binary
  actually lives, not only in this file:
  * `bin/windows/LICENSE.seqtk.txt` - byte-identical to the upstream `LICENSE`
    file, next to the `.exe` in the source form;
  * the same file, plus `LICENSE.txt`, are bundled inside the packaged form (see
    the PyInstaller section).
* Upstream links: [LICENSE](https://github.com/lh3/seqtk/blob/master/LICENSE),
  [release 1.5](https://github.com/lh3/seqtk/releases/tag/v1.5).

**Verifying the bundled binary.** Anyone can check that `seqtk.exe` corresponds
to the published build recipe instead of taking it on faith:

```powershell
sha256sum bin/windows/seqtk.exe
# b844d8f0cee53681903f71848207d8ddace051d6aee51e79d1a49431bfe9846d
tools\seqtk-build\build_seqtk_windows.bat C:\path\to\seqtk-1.5   # rebuild
bin\windows\seqtk.exe            # must print "Version: 1.5-r133"
```

The upstream `LICENSE` file is reproduced verbatim, typographical error in the
copyright line included, and deliberately **not** corrected:

```text
The MIT License
Copyright (c) 20082-2012 by Heng Li <lh3@me.com>
Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:
The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

Note that the email address above is part of the upstream copyright notice that
MIT obliges us to reproduce; it is Heng Li's, not a contributor's, and no
personal contact details of this project's authors are published anywhere.

### kseq.h and khash.h (compiled into `seqtk.exe`)

`bin/windows/seqtk.exe` is not built from `seqtk.c` alone. Upstream `seqtk.c`
does `#include "kseq.h"` and `#include "khash.h"`, and the upstream `Makefile`
lists both headers as prerequisites of the target
(`seqtk:seqtk.c khash.h kseq.h`). They are compiled into the distributed binary
as part of it, so that binary is a copy of those two libraries just as much as
it is a copy of seqtk - and MIT binds the copyright and permission notices to
*all copies or substantial portions*, binaries included.

* Projects: <https://github.com/attractivechaos/klib> (`khash.h`, `kseq.h`)
* Author: Attractive Chaos
* License: MIT
* Obligations carried: the notice of each header is reproduced verbatim below,
  exactly as it sits at the top of its own file. The two copyright lines are
  worded differently - `khash.h` has "2008, 2009, 2011 **by** Attractive Chaos",
  `kseq.h` has "2008, 2009, 2011 Attractive Chaos" without the "by" - and the
  difference is preserved rather than normalised, because a verbatim notice is
  copied, not rewritten. The same two blocks appear in
  [LICENSE.txt](../LICENSE.txt), which is bundled inside the packaged form, so
  the notice travels with both distribution forms.

`khash.h`:

```text
/* The MIT License

   Copyright (c) 2008, 2009, 2011 by Attractive Chaos <attractor@live.co.uk>

   Permission is hereby granted, free of charge, to any person obtaining
   a copy of this software and associated documentation files (the
   "Software"), to deal in the Software without restriction, including
   without limitation the rights to use, copy, modify, merge, publish,
   distribute, sublicense, and/or sell copies of the Software, and to
   permit persons to whom the Software is furnished to do so, subject to
   the following conditions:

   The above copyright notice and this permission notice shall be
   included in all copies or substantial portions of the Software.

   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
   MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
   NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
   BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
   ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
   CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
   SOFTWARE.
*/
```

`kseq.h`:

```text
/* The MIT License

   Copyright (c) 2008, 2009, 2011 Attractive Chaos <attractor@live.co.uk>

   Permission is hereby granted, free of charge, to any person obtaining
   a copy of this software and associated documentation files (the
   "Software"), to deal in the Software without restriction, including
   without limitation the rights to use, copy, modify, merge, publish,
   distribute, sublicense, and/or sell copies of the Software, and to
   permit persons to whom the Software is furnished to do so, subject to
   the following conditions:

   The above copyright notice and this permission notice shall be
   included in all copies or substantial portions of the Software.

   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
   MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
   NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
   BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
   ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
   CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
   SOFTWARE.
*/
```

The email addresses above belong to the authors of those headers and are
reproduced only because their licenses require the notice to be kept intact.

## Qt / PySide6 / Shiboken

* Projects: <https://www.qt.io>, <https://pypi.org/project/PySide6/>,
  <https://pypi.org/project/shiboken6/>
* License as published upstream: `LGPL-3.0-only OR GPL-2.0-only OR
  GPL-3.0-only` (read from the installed distribution metadata of PySide6 and
  shiboken6). **This project chooses the LGPL-3.0-only option**, so the terms
  below are LGPL-3.0-only terms.
* `shiboken6` is not an optional extra: PySide6 is a generated C++/Python
  binding layer and `shiboken6` (its `.dll`) is the runtime that makes every
  `PySide6.Qt*` import work, so it is part of the same LGPL-licensed object code
  and carries the identical obligations.
* What is used: the GUI toolkit, as an installed dependency in the source form,
  and as **redistributed binaries in the packaged form**. The archive inside
  `dist/SeqTK-GUI.exe` carries **92 `.dll` entries**. 46 of them sit under
  `PySide6\` and `shiboken6\` - `Qt6Core.dll`, `Qt6Gui.dll`, `Qt6Widgets.dll`,
  `Shiboken.dll`, the Qt plugin DLLs under `PySide6\plugins\`, and the Microsoft
  VC runtime files those wheels ship. The other 46 sit at the archive root: the
  two CPython interpreter DLLs, the three OpenSSL DLLs, two further
  `VCRUNTIME140*.dll` and the 39 Windows UCRT app-local DLLs (see the sections
  below). Count them yourself:

  ```powershell
  python -c "from PyInstaller.archive.readers import CArchiveReader as R; d=[n for n in R('dist/SeqTK-GUI.exe').toc if n.lower().endswith('.dll')]; print(len(d))"
  ```

### What LGPL-3.0 actually requires here

LGPL-3.0 §4 (*Combined Works*) requires, when conveying a combined work in
object-code form:

1. a **prominent notice** that the work uses the Library and that the Library
   and its use are covered by the LGPL;
2. a copy of **both** the GNU GPL and the GNU LGPL license documents;
3. the Library's copyright notice among the notices displayed at run time, with
   a reference pointing to those two license copies;
4. **one** of two ways to preserve the user's freedom to modify and relink:
   * 0) convey the Minimal Corresponding Source of the Library plus the
     Corresponding Application Code in a form that lets the user recombine or
     relink, **or**
   * 1) use a *suitable shared library mechanism* - i.e. keep the Library as a
     separate, dynamically linked object that will operate against a
     modified, interface-compatible version of the Library.

PySide6 ships Qt as separate DLLs and the app binds to them at run time, so the
**shared-library route 1)** is the one this project relies on. That has an
important consequence for the question this section exists to answer:

> Does a PyInstaller *onefile* build have to ship the Qt/PySide6 source, or a
> compilable source form, to satisfy LGPL-3.0?

**No - source is not required, provided the shared-library conditions hold.**
§4(d) is an "either/or": option 1) exists precisely so that a dynamically linked
application can be conveyed without the library's source. "Provide a written
offer with instructions on how to obtain the source" is the route for the
*source* alternative 0), and merely linking to the vendor's website is not
accepted as a substitute for the notice and license-text duties in 1)-3). So the
binding obligations are the **notice, the two license texts, the run-time
attribution, and genuine replaceability of the library** - not shipping Qt's
source tree.

### What the onefile form does and does not satisfy

Onefile unpacks everything into a temporary `_MEIxxxxxx` directory at start-up
and deletes it on exit. That does not break §4(d)(1) by itself - the payload
still consists of individually loaded DLLs rather than objects merged into one
binary - but it does two things that matter:

* it makes the separation less practical to exploit, because a user cannot
  simply drop a rebuilt `Qt6Core.dll` next to the file they downloaded;
* it makes the *notice* duties easy to miss, and they are not satisfied by
  accident. Nothing in this area arrives on its own: the installed PySide6
  6.12.0 distribution carries **no LGPL or GPL text to collect** - the
  `PySide6` package directory itself holds no license file, and the
  `licenses/` directory that does exist is the one inside `*.dist-info`, whose
  single entry `LicenseRef-Qt-Commercial.txt` is a commercial-license notice
  pointing at <https://www.qt.io/terms-conditions>, not a copy of any GPL or
  LGPL. Nor does PyInstaller add one: every path in the finished manifest that
  contains `LICENSE`, `COPYING`, `LGPL` or `GPL` is present only because
  `packaging/SeqTK-GUI.spec` lists it explicitly. That disproves the assumption
  that the Qt license texts are collected automatically.

Therefore, for a compliant packaged release all of the following must hold, and
`packaging/SeqTK-GUI.spec` arranges the first three mechanically:

* `LICENSE.txt`, `bin/windows/LICENSE.seqtk.txt` and the license texts in
  `packaging/licenses/` (GNU LGPL-3.0, GNU GPL-3.0, zlib) are bundled into the
  application, so they accompany the combined work;
* the **About** dialog shows this status prominently and renders the license
  text at run time, satisfying the prominent-notice and run-time-attribution
  duties;
* a **folder build is offered** (`ONEFILE=0 tools\build_exe_windows.bat`), in
  which the Qt DLLs sit beside the executable and a user can verify and replace
  them; the source form of this project always satisfies this because it merely
  imports a user-installed PySide6;
* the exact PySide6 version used is stated here and is reproducible from
  `requirements.txt` (`PySide6>=6.5,<7`), and the full official source remains
  obtainable from <https://www.qt.io/download-open-source> and
  <https://download.qt.io/official_releases/qt/> - provided as context, not as
  a substitute for the obligations above.

## zlib

* Project: <https://www.zlib.net>, <https://github.com/madler/zlib>
* License: zlib license (SPDX `Zlib`); text in
  `packaging/licenses/Zlib.txt`
* What is used: seqtk's only library dependency. It is **statically linked into
  the bundled `bin/windows/seqtk.exe`** - that binary imports only
  `KERNEL32.dll`, `USER32.dll` and `msvcrt.dll` while containing the
  `deflate*` symbols and reading `.gz` input successfully, which shows the zlib
  code is inside the distributed file rather than fetched at run time.
* Obligations carried: the three zlib restrictions must accompany the binary.
  This project does not claim authorship of zlib, does not misrepresent altered
  versions, and does not remove the notice - the license text ships next to the
  `.exe` and inside the package.
* Note for anyone rebuilding: with a toolchain that links zlib dynamically you
  would have to ship `zlib1.dll` too; the build script relies on the static
  library, which is why this entry exists at all.

## Python / CPython

* Project: <https://www.python.org>
* License: Python Software Foundation License (PSF-2.0)
* What is used: the interpreter. In the source form the user installs it. In the
  packaged form the CPython runtime is embedded in `dist/SeqTK-GUI.exe`, so the
  PSF license travels with it; its text is at
  <https://docs.python.org/3/license.html>.

## OpenSSL

Three OpenSSL DLLs are redistributed inside `dist/SeqTK-GUI.exe`. None of them
comes from this project's own code - nothing here calls OpenSSL directly - they
are runtime dependencies of the CPython and Qt binaries the build already
embeds, and PyInstaller's dependency scan collected them alongside those:

| DLL inside the package | Version | What needs it | License |
| --- | --- | --- | --- |
| `libcrypto-1_1.dll` | OpenSSL 1.1.1m | CPython's `_hashlib.pyd` | OpenSSL License + SSLeay License (dual permissive) |
| `libcrypto-3-x64.dll` | OpenSSL 3.5.4 | `PySide6\plugins\tls\qopensslbackend.dll` | Apache License 2.0 |
| `libssl-3-x64.dll` | OpenSSL 3.5.4 | the same Qt TLS plugin | Apache License 2.0 |

* Project: <https://www.openssl.org>
* What is used: the TLS/hash back ends of the embedded CPython and Qt binaries.
  The 1.1.1m copy is a build artifact of the CPython interpreter that ships in
  the package; the 3.x pair is what Qt's OpenSSL TLS plugin resolves to on the
  machine that built the package. The source form redistributes no OpenSSL file.
* Obligations carried: both license families are permissive and require their
  notice to accompany the distributed binaries. Full texts:
  <https://www.openssl.org/source/license.html> (1.1.x, dual OpenSSL/SSLeay) and
  <https://www.apache.org/licenses/LICENSE-2.0> (3.x).
* Neither is linked into anything this project wrote, and neither appears in the
  repository; the redistribution happens only through the packaged build.

## PyInstaller (build tool and embedded runtime pieces)

* Project: <https://pyinstaller.org>
* License of the tool itself: GPL-2.0-or-later
  (<https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt>).
* The **Bootloader Exception** in that `COPYING.txt` is narrower than "the
  output may be distributed under any terms whatsoever", and its own wording is
  what applies: the authors give "unlimited permission to link or embed compiled
  bootloader and related files into combinations with other programs, and to
  distribute those combinations *without any restriction coming from the use of
  those files*", and the same sentence continues "(The General Public License
  restrictions **do apply in other respects**; for example, they cover
  modification of the files, and distribution when not linked into a combined
  executable.)". So the produced program is not encumbered *by those files* -
  it does not follow that the GPL stops governing the PyInstaller files
  themselves, whose modification and standalone distribution remain under GPL.
* "Bootloader and related files", as that document defines them, are the files
  embedded in the final executable, namely `./bootloader/` and
  `./PyInstaller/loader/`. This build embeds precisely those: `main`,
  `pyiboot01_bootstrap`, `pyimod01_archive`, `pyimod02_importers`,
  `pyimod03_ctypes` and `pyimod04_pywin32`.
* **Run-time hooks carry a different license.** The same `COPYING.txt` states
  that run-time hooks (`./PyInstaller/hooks/rthooks`) and the additional
  run-time modules from `./PyInstaller/fake-modules` - `pyi_splash` and the
  `_pyi_rth_utils` utility package - "are licensed under the Apache License,
  Version 2.0". This build embeds `pyi_rth_inspect`, `pyi_rth_pyside6`,
  `_pyi_rth_utils` and `_pyi_rth_utils.qt`, so Apache-2.0 code sits inside the
  packaged artifact next to the GPL-excepted bootloader pieces.
* What is used: a build-time tool. The PyInstaller package and its CLI are not
  redistributed; only the files listed above are embedded, each under its own
  terms. `seqtk_gui/` is original work under this project's MIT license, and
  combining it with those embedded pieces is exactly what the Bootloader
  Exception permits.

## MinGW runtime / MSVC CRT / Windows UCRT

The two distribution forms differ here, so they are separated.

* **Source form.** `seqtk.exe` and the Qt DLLs rely on the platform C runtime
  (`msvcrt.dll` ships with Windows) and, where relevant, on the MinGW runtime
  included in the compiler the user installs. Neither is added to the
  repository by this project.
* **Packaged form - Microsoft Visual C++ runtime.** `dist/SeqTK-GUI.exe` does
  redistribute these as files of its own: 10 DLL entries in total -
  `MSVCP140.dll`, `MSVCP140_1.dll`, `MSVCP140_2.dll`, `VCRUNTIME140.dll` and
  `VCRUNTIME140_1.dll` under `PySide6\`; `MSVCP140.dll`, `VCRUNTIME140.dll` and
  `VCRUNTIME140_1.dll` under `shiboken6\`; and `VCRUNTIME140.dll` plus
  `VCRUNTIME140_1.dll` at the archive root beside the CPython binaries.
  They arrive because the PySide6, shiboken6 and CPython wheels ship them as
  redistributable components; they are proprietary Microsoft binaries covered by
  the Microsoft Visual C++ runtime redistributable license terms, not by any
  open-source license, and this project obtained them only as installed
  dependencies.
* **Packaged form - Windows UCRT.** The same archive carries 39 further C
  runtime DLLs: 38 `api-ms-win-*.dll` app-local API-set stubs and `ucrtbase.dll`,
  collected from `C:\WINDOWS\System32` by the packaging step. These are Windows
  components under the Windows license terms; the source form copies none of
  them.
* Obligations carried: none of the three groups above is relicensed here. The
  VC runtime and UCRT files travel as unmodified Microsoft binaries that the
  distributions they came from already permit to be redistributed, which is why
  they are named explicitly rather than left implicit.

## Where the license files live

| File | Source form | Packaged form |
| --- | --- | --- |
| project MIT + seqtk, khash.h and kseq.h notices | `LICENSE.txt` | `LICENSE.txt` |
| seqtk upstream notice beside the binary | `bin/windows/LICENSE.seqtk.txt` | `LICENSE.seqtk.txt` |
| this page | `docs/THIRD_PARTY_NOTICES.md`, `docs/THIRD_PARTY_NOTICES.zh-CN.md` | both files at the top level |
| GNU LGPL-3.0 | `packaging/licenses/LGPL-3.0-only.txt` | `licenses/LGPL-3.0-only.txt` |
| GNU GPL-3.0 | `packaging/licenses/GPL-3.0-only.txt` | `licenses/GPL-3.0-only.txt` |
| zlib | `packaging/licenses/Zlib.txt` | `licenses/Zlib.txt` |

In the onefile build these sit inside the archive and are unpacked to the
temporary `_MEIxxxxxx` directory while the app runs; in the folder build
(`ONEFILE=0`) they are ordinary files next to the executable, which is the form
to hand out if you want users to be able to inspect and replace the Qt DLLs.
The **About** dialog renders `LICENSE.txt` followed by this page for the current
UI language, which is where the run-time notice required by LGPL-3.0 §4 is made.

## No other code is derived from elsewhere

The command spec, the GUI, the MinGW PRNG shim and the tests were written for
this repository. The shim implements the documented POSIX algorithm rather than
copying an existing implementation.
