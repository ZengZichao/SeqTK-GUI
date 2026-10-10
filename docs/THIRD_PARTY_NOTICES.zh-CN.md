# 第三方组件与许可声明

SeqTK-GUI 采用 MIT 许可（见 [LICENSE.txt](../LICENSE.txt)）。它是一个独立的
**非官方**作品，只调用其他程序；下列组件仍适用各自的许可条款，在此列出以便随仓库
以及随打包后的程序一起传播。

本项目存在两种分发形态，各自的义务不同，因此每一条目都注明它影响哪种形态：

* **源码形态** —— `git clone` 得到的内容（Python 代码 + 文档 +
  `bin/windows/seqtk.exe`）。
* **打包形态** —— `dist/SeqTK-GUI.exe`，PyInstaller **单文件（onefile）** 构建产物，
  内嵌 CPython 运行时、PySide6 与 Qt 6 的 DLL，以及 `bin/windows/seqtk.exe`。
  LGPL 的义务正是在这里生效。

## seqtk

* 项目地址：<https://github.com/lh3/seqtk>
* 作者：Heng Li
* 本项目对齐的版本：**1.5-r133**
* 许可：MIT
* 使用方式（两种形态均涉及）：
  * `seqtk_gui/core/spec.py` 与 [COMMANDS.zh-CN.md](COMMANDS.zh-CN.md) 转写了 seqtk 的
    `getopt()` 选项串、默认值与帮助文本，属于 seqtk 的衍生作品，因此这部分仍适用
    seqtk 的 MIT 许可，而不是本项目的许可。
  * `bin/windows/seqtk.exe` 是 **seqtk 的二进制副本**：由未经改动的上游 `seqtk.c`
    加上一个本项目的兼容文件 `tools/seqtk-build/mingw_prng_shim.c` 编译而来
    （见 [BUILD_SEQTK.zh-CN.md](BUILD_SEQTK.zh-CN.md)）。这使它构成 seqtk 的修改版本，
    因此本文档明确标注该改动——MIT 的衍生条款与 zlib 的条款都如此要求。seqtk 从不
    链接进 Python 进程，本项目也不会对其重新授权。
* 承担的义务：MIT 要求版权声明与许可声明必须包含在软件的**所有副本或实质部分**中。
  二进制文件就是这样一个副本，所以逐字声明要放在二进制实际所在的位置，而不只是写在
  本文件里：
  * `bin/windows/LICENSE.seqtk.txt` —— 与上游 `LICENSE` 文件逐字节一致，在源码形态中
    紧邻该 `.exe`；
  * 同一个文件加上 `LICENSE.txt`，会被打包进最终程序（见下文 PyInstaller 一节）。
* 上游链接：[LICENSE](https://github.com/lh3/seqtk/blob/master/LICENSE)、
  [1.5 版本发布页](https://github.com/lh3/seqtk/releases/tag/v1.5)。

**校验随附的二进制。** 任何人都可以核实 `seqtk.exe` 确实出自公开的构建流程，而不必
凭信任接受它：

```powershell
sha256sum bin/windows/seqtk.exe
# b844d8f0cee53681903f71848207d8ddace051d6aee51e79d1a49431bfe9846d
tools\seqtk-build\build_seqtk_windows.bat C:\path\to\seqtk-1.5   # 重新编译
bin\windows\seqtk.exe            # 应输出 "Version: 1.5-r133"
```

以下是逐字复制的上游 `LICENSE` 文本，其中版权行的拼写错误原样保留，且**刻意不做修正**：

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

请注意：上述邮箱地址是 MIT 要求我们逐字保留的上游版权声明的一部分，它属于 Heng Li，
并非本项目的贡献者；本项目作者的私人联系方式未在仓库任何位置发布。

### 编译进 `seqtk.exe` 的 kseq.h 与 khash.h

`bin/windows/seqtk.exe` 并非只由 `seqtk.c` 编译而成。上游 `seqtk.c` 里有
`#include "kseq.h"` 与 `#include "khash.h"`，上游 `Makefile` 也把这两个头文件列为
构建目标的前置依赖（`seqtk:seqtk.c khash.h kseq.h`）。它们作为该二进制的一部分被
编译进去，因此那份二进制既是 seqtk 的副本，也是这两个库的副本——而 MIT 要求版权
声明与许可声明保留在软件的**所有副本或实质部分**中，二进制副本同样算副本。

* 项目地址：<https://github.com/attractivechaos/klib>（`khash.h`、`kseq.h`）
* 作者：Attractive Chaos
* 许可：MIT
* 承担的义务：两个头文件各自的声明在下方逐字复制，与其源文件开头保持一致。两行
  版权行的措辞并不相同——`khash.h` 作 "2008, 2009, 2011 **by** Attractive Chaos"，
  `kseq.h` 作 "2008, 2009, 2011 Attractive Chaos"，没有 "by"——这一差异按原文保留而
  不做统一，因为逐字保留意味着照抄而非改写。同样的两段文本也出现在
  [LICENSE.txt](../LICENSE.txt) 中，而该文件会被打包进最终程序，因此声明随两种
  分发形态一同传播。

`khash.h`：

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

`kseq.h`：

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

上述邮箱地址属于这两个头文件的作者，之所以出现，只是因为其许可要求声明保持完整。

## Qt / PySide6 / Shiboken

* 项目地址：<https://www.qt.io>、<https://pypi.org/project/PySide6/>、
  <https://pypi.org/project/shiboken6/>
* 上游发布的许可：`LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only`（读取自已安装的
  PySide6 与 shiboken6 的分发元数据）。**本项目选择 LGPL-3.0-only 这一选项**，
  因此下述条款均为 LGPL-3.0-only 的条款。
* `shiboken6` 不是可选的附属品：PySide6 是自动生成的 C++/Python 绑定层，而
  `shiboken6`（它的 `.dll`）是让所有 `PySide6.Qt*` 导入得以工作的运行时，因此它与
  Qt 同属受 LGPL 约束的目标代码，承担完全相同的义务。
* 使用方式：源码形态中作为已安装的依赖导入；打包形态中作为**再分发的二进制**。
  `dist/SeqTK-GUI.exe` 内部的归档带着 **92 个 `.dll` 条目**：其中 46 个位于
  `PySide6\` 与 `shiboken6\` 之下——`Qt6Core.dll`、`Qt6Gui.dll`、`Qt6Widgets.dll`、
  `Shiboken.dll`、`PySide6\plugins\` 下的各 Qt 插件 DLL，以及这两个 wheel 自带的
  微软 VC 运行库文件；另外 46 个位于归档根部：CPython 解释器的两个 DLL、三个
  OpenSSL DLL、再两个 `VCRUNTIME140*.dll`，以及 39 个 Windows UCRT 的 app-local
  DLL（见下文相应小节）。可自行核验：

  ```powershell
  python -c "from PyInstaller.archive.readers import CArchiveReader as R; d=[n for n in R('dist/SeqTK-GUI.exe').toc if n.lower().endswith('.dll')]; print(len(d))"
  ```

### LGPL-3.0 在这里到底要求什么

LGPL-3.0 第 4 条（*组合作品 Combined Works*）规定，以目标代码形态传播组合作品时：

1. 必须给出**显著声明**，说明该作品使用了本库，且本库及其使用受 LGPL 约束；
2. 同时附上 **GNU GPL 与 GNU LGPL 两份许可文件**；
3. 若程序在运行期间显示版权声明，须在其中包含本库的版权声明，并给出指向上述两份
   许可文件的指引；
4. 二选一，以保障用户修改并重新链接的自由：
   * 0) 传播本库的 Minimal Corresponding Source，以及 Corresponding Application
     Code，且其形式与条款允许用户将修改过的本库版本与应用程序重新组合或重新链接；**或**
   * 1) 使用*合适的共享库机制*——即把本库保持为独立、动态链接的目标文件，使其能够
     针对接口兼容的修改版本正常工作。

PySide6 把 Qt 以独立 DLL 形式提供，应用在运行时绑定这些 DLL，因此本项目依赖的是
**共享库路径 1)**。这对本节要回答的问题有直接结论：

> PyInstaller **单文件（onefile）** 构建是否必须随附 Qt/PySide6 的源码或可编译源码，
> 才能满足 LGPL-3.0？

**不需要——在共享库条件成立时，源码不是必需项。** 第 4(d) 条是"二选一"结构：设置
选项 1) 的意义恰恰在于让动态链接的应用可以不带库源码就传播。"提供书面要约说明如何
获取源码"是*源码*路径 0) 下的做法；而仅仅链接到厂商官网，并不能替代第 1)–3) 项的
声明与许可文件义务。因此真正具有约束力的义务是**显著声明、两份许可文件、运行时署名，
以及库确实可被替换**——而不是搬运 Qt 的源码树。

### 单文件形态满足了什么、没满足什么

onefile 在启动时把全部内容解压到临时目录 `_MEIxxxxxx`，退出时删除。单就这一点并不
破坏第 4(d)(1) 条——载荷仍然是一组各自独立加载的 DLL，而非合并进单一二进制——但它
确实在两方面有影响：

* 它使"分离"在实操上更难利用，因为用户无法把重新编译的 `Qt6Core.dll` 直接放到下载
  的文件旁边；
* 它让*声明类*义务很容易被漏掉，而这些义务不会自动满足。这一带没有任何内容是
  自己冒出来的：已安装的 PySide6 6.12.0 发行包里**没有可收集的 LGPL 或 GPL 文本**
  ——`PySide6` 包目录本身不含任何许可文件，而确实存在的 `licenses/` 目录是
  `*.dist-info` 里的那个，其中唯一的一份文件 `LicenseRef-Qt-Commercial.txt` 是
  指向 <https://www.qt.io/terms-conditions> 的商业许可告知，并不是任何 GPL 或 LGPL
  的副本。PyInstaller 也不会补上：最终构建清单里凡含 `LICENSE`、`COPYING`、`LGPL`、
  `GPL` 的路径，全都只因 `packaging/SeqTK-GUI.spec` 显式列出才在。这直接否定了
  "Qt 的许可文本会被自动带入"这一假设。

因此，要让打包发布合规，下列各项都必须成立，而 `packaging/SeqTK-GUI.spec` 把前三项
变成机械可保证的事情：

* `LICENSE.txt`、`bin/windows/LICENSE.seqtk.txt` 以及 `packaging/licenses/` 下的许可
  文本（GNU LGPL-3.0、GNU GPL-3.0、zlib）会被一并打包进程序，从而随组合作品传播；
* **关于**对话框会显著展示本项目的非官方状态，并在运行时渲染许可文本，以满足显著声明
  与运行时署名义务；
* **同时提供文件夹形态构建**（`ONEFILE=0 tools\build_exe_windows.bat`），在该形态中
  Qt 的 DLL 与可执行文件并列，用户可以直接核验并替换它们；本项目的源码形态始终满足
  这一条，因为它只是导入用户自行安装的 PySide6；
* 实际使用的 PySide6 版本在此说明，并可由 `requirements.txt`（`PySide6>=6.5,<7`）
  复现；Qt 的完整官方源码仍可从 <https://www.qt.io/download-open-source> 与
  <https://download.qt.io/official_releases/qt/> 获取——这是补充说明，而不是上述义务的
  替代方案。

## zlib

* 项目地址：<https://www.zlib.net>、<https://github.com/madler/zlib>
* 许可：zlib 许可（SPDX 标识 `Zlib`）；文本见 `packaging/licenses/Zlib.txt`
* 使用方式：seqtk 唯一的库依赖。它被**静态链接进了随仓库提供的
  `bin/windows/seqtk.exe`**——该二进制只导入 `KERNEL32.dll`、`USER32.dll` 与
  `msvcrt.dll`，却包含 `deflate*` 符号并能成功读取 `.gz` 输入，说明 zlib 的代码在
  分发的那份文件里，而不是运行时另行获取。
* 承担的义务：zlib 的三条限制必须随二进制一起传播。本项目不宣称 zlib 由我们所写，
  不隐瞒版本改动，也不移除声明——许可文本与该 `.exe` 并列存放，也在包内。
* 重新编译者注意：若你的工具链以动态方式链接 zlib，则还需一并分发 `zlib1.dll`；
  构建脚本依赖的是静态库，这正是本条目存在的原因。

## Python / CPython

* 项目地址：<https://www.python.org>
* 许可：Python Software Foundation License（PSF-2.0）
* 使用方式：运行本界面的解释器。源码形态下由使用者自行安装；打包形态下 CPython 运行时
  被内嵌进 `dist/SeqTK-GUI.exe`，因此 PSF 许可需随之传播，其文本见
  <https://docs.python.org/3/license.html>。

## OpenSSL

`dist/SeqTK-GUI.exe` 内部再分发三个 OpenSSL 的 DLL。它们都不是本项目自己的代码带进来的
——本项目没有直接调用 OpenSSL——而是包内已内嵌的 CPython 与 Qt 二进制所依赖的运行时
组件，由 PyInstaller 的依赖扫描一并收集而来：

| 包内 DLL | 版本 | 依赖它的一方 | 许可 |
| --- | --- | --- | --- |
| `libcrypto-1_1.dll` | OpenSSL 1.1.1m | CPython 的 `_hashlib.pyd` | OpenSSL 许可证 + SSLeay 许可证（双许可，宽松） |
| `libcrypto-3-x64.dll` | OpenSSL 3.5.4 | `PySide6\plugins\tls\qopensslbackend.dll` | Apache License 2.0 |
| `libssl-3-x64.dll` | OpenSSL 3.5.4 | 同上（Qt 的 TLS 插件） | Apache License 2.0 |

* 项目地址：<https://www.openssl.org>
* 使用方式：包内内嵌的 CPython 与 Qt 二进制之 TLS/摘要后端。1.1.1m 那份是打包所用的
  CPython 解释器自带的构建产物；3.x 那一对是 Qt 的 OpenSSL TLS 插件在构建机上解析到
  的版本。源码形态不再分发任何 OpenSSL 文件。
* 承担的义务：两套许可都是宽松许可，要求其声明随所分发的二进制一同传播。完整文本见
  <https://www.openssl.org/source/license.html>（1.1.x，OpenSSL/SSLeay 双许可）与
  <https://www.apache.org/licenses/LICENSE-2.0>（3.x）。
* 这两组文件都不与本项目编写的任何代码静态链接，也不出现在仓库里；再分发只经由
  打包产物发生。

## PyInstaller（构建工具与其嵌入运行时的各部件）

* 项目地址：<https://pyinstaller.org>
* 工具本体的许可：GPL-2.0-or-later
  （<https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt>）。
* 该 `COPYING.txt` 里的 **Bootloader Exception**（引导器例外）比"产物可以任何条款
  分发"更窄，应当以它自己的措辞为准：作者授予"不受限制地把已编译的引导器及相关文件
  链接或嵌入到其他程序的组合体中，并分发这些组合体，*不因使用这些文件而带来任何
  限制*"，而同一句紧接着写道"（GNU 通用公共许可的其他限制*仍然适用*；例如，它们覆盖
  对这些文件的修改，以及未链接进可执行组合体时的分发。）"。也就是说，被免除的只是
  *因这些文件而起*的限制，并不等于 GPL 对 PyInstaller 那些文件本身失去约束——修改它们、
  或单独分发它们，是另一回事。
* 按该文件的定义，"引导器及相关文件"就是会被嵌入最终可执行文件的那些内容，即
  `./bootloader/` 与 `./PyInstaller/loader/`。本构建嵌入的正是这些：`main`、
  `pyiboot01_bootstrap`、`pyimod01_archive`、`pyimod02_importers`、`pyimod03_ctypes`
  与 `pyimod04_pywin32`。
* **运行时钩子适用另一份许可。** 同一份 `COPYING.txt` 声明：运行时钩子
  （`./PyInstaller/hooks/rthooks`）以及来自 `./PyInstaller/fake-modules` 的额外运行时
  模块——`pyi_splash` 与 `_pyi_rth_utils` 工具包——"依 Apache 许可证 2.0 版授权"。
  本构建嵌入了 `pyi_rth_inspect`、`pyi_rth_pyside6`、`_pyi_rth_utils` 与
  `_pyi_rth_utils.qt`，因此打包产物里除了受引导器例外覆盖的部分，还含有 Apache-2.0
  的代码。
* 使用方式：只在构建期使用的工具。PyInstaller 的 Python 包与其命令行本身不会被
  再分发；被嵌入的只有上面逐项列出的文件，各自适用其自身条款。`seqtk_gui/` 是本
  项目原创、按本项目 MIT 许可发布的作品，把它与上述嵌入部件组合起来恰好是
  Bootloader Exception 所允许的情形。

## MinGW 运行时 / MSVC CRT / Windows UCRT

两种分发形态在这一节的情况不同，因此分开说明。

* **源码形态。** `seqtk.exe` 与 Qt 的 DLL 依赖平台的 C 运行库（`msvcrt.dll` 由
  Windows 自带），在相关情况下也依赖用户所装编译器自带的 MinGW 运行时。这两者都不是
  本项目加入仓库的内容。
* **打包形态——微软 Visual C++ 运行库。** `dist/SeqTK-GUI.exe` 确实把它们作为独立
  文件再分发了：共 10 个 DLL 条目——`PySide6\` 下的 `MSVCP140.dll`、
  `MSVCP140_1.dll`、`MSVCP140_2.dll`、`VCRUNTIME140.dll`、`VCRUNTIME140_1.dll`；
  `shiboken6\` 下的 `MSVCP140.dll`、`VCRUNTIME140.dll`、`VCRUNTIME140_1.dll`；
  以及归档根部紧邻 CPython 二进制的 `VCRUNTIME140.dll` 与 `VCRUNTIME140_1.dll`。
  它们之所以出现，是因为 PySide6、shiboken6 与 CPython 的 wheel 把它们作为可再分发
  组件一并自带；它们是微软的专有二进制，适用微软 Visual C++ 运行库再分发许可条款，
  而不属于任何开源许可，本项目只是作为已安装依赖取得它们。
* **打包形态——Windows UCRT。** 同一个归档里还有 39 个其他 C 运行库 DLL：38 个
  `api-ms-win-*.dll` app-local API set 桩文件与 `ucrtbase.dll`，由打包环节从
  `C:\WINDOWS\System32` 收集而来。它们是 Windows 组件，适用 Windows 许可条款；
  源码形态不复制其中任何一个。
* 承担的义务：以上三组都不在此重新授权。VC 运行库与 UCRT 文件以未经修改的微软
  二进制形式传播，而它们来源的那个发行版本就已允许这类再分发，因此这里点名列出，
  而不是含糊带过。

## 许可文件的存放位置

| 文件 | 源码形态 | 打包形态 |
| --- | --- | --- |
| 本项目 MIT + seqtk、khash.h 与 kseq.h 声明 | `LICENSE.txt` | `LICENSE.txt` |
| 与二进制并列的上游 seqtk 声明 | `bin/windows/LICENSE.seqtk.txt` | `LICENSE.seqtk.txt` |
| 本页 | `docs/THIRD_PARTY_NOTICES.md`、`docs/THIRD_PARTY_NOTICES.zh-CN.md` | 两个文件均置于顶层 |
| GNU LGPL-3.0 | `packaging/licenses/LGPL-3.0-only.txt` | `licenses/LGPL-3.0-only.txt` |
| GNU GPL-3.0 | `packaging/licenses/GPL-3.0-only.txt` | `licenses/GPL-3.0-only.txt` |
| zlib | `packaging/licenses/Zlib.txt` | `licenses/Zlib.txt` |

单文件形态下这些文件位于包内归档中，程序运行时被解压到临时的 `_MEIxxxxxx` 目录；
文件夹形态（`ONEFILE=0`）下它们是可执行文件旁边的普通文件——若你希望用户能够核验
并替换 Qt 的 DLL，应发放这一形态。**关于**对话框会先渲染 `LICENSE.txt`，随后按当前
界面语言接上本页内容，LGPL-3.0 第 4 条要求的运行时声明即在此处完成。

## 其他代码来源

命令规格、界面、MinGW 的 PRNG 补丁与测试均为本仓库原创。PRNG 补丁按 POSIX 文档定义的
算法实现，未复制任何既有实现代码。
