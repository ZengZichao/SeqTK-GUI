# 编译 seqtk 可执行文件

界面自己绝不解析或转换序列，因此必须有本地的 seqtk 程序。仓库提供
`bin/windows/seqtk.exe`，由未经改动的上游 `seqtk.c`（1.5-r133）编译而来。
生成它的过程中没有修改 `seqtk-1.5/` 里的任何文件，唯一新增的是下面提到的兼容补丁。

## Windows

前置条件：带 zlib 的 MinGW-w64 gcc（Strawberry Perl 自带的一套可用，MSYS2 的
`mingw-w64-ucrt-x86_64-gcc` 加 `mingw-w64-ucrt-x86_64-zlib` 也可以）。

作为参照，仓库内 `bin/windows/seqtk.exe` 里带着两个编译器标识，弄清它们的来源对
复现构建很关键：`GCC: (x86_64-posix-seh, Built by strawberryperl.com project)
8.3.0` 是真正编译 `seqtk.c` 与补丁的编译器；`GCC: (x86_64-posix-seh-rev1, Built
by MinGW-W64 project) 7.2.0` 来自被链接进来的 MinGW-W64 预编译运行时目标文件，
并不代表工具链是 7.2.0。zlib 1.2.11 以静态方式链接。任何等价工具链都能编译出可用
的程序；只有下面那个校验和与上述那一次构建绑定。

上述流程已实际重跑过一次：产物的字节大小一致，且在 `python tools\probe_seqtk.py`
覆盖的每一个子命令与选项上与随仓库发布的二进制**行为完全相同**，只是 SHA-256 不同
——目标文件顺序与内嵌路径每次都会变。这才是这里“可复现”的实际含义：可核验的行为，
而不是一模一样的字节。

```powershell
tools\seqtk-build\build_seqtk_windows.bat C:\path\to\seqtk-1.5
```

等价于：

```powershell
gcc -g0 -O2 -Wall -Wno-unused-function -Wno-format ^
    -ffile-prefix-map=<seqtk 源码目录>=seqtk-1.5 ^
    -ffile-prefix-map=<仓库目录>\tools\seqtk-build=tools/seqtk-build ^
    <seqtk 源码目录>\seqtk.c tools\seqtk-build\mingw_prng_shim.c ^
    -o bin\windows\seqtk.exe -lz -lm
```

`-g0` 与两条 `-ffile-prefix-map` 不是可选项。这个二进制会随仓库发布，而只加 `-g`
的编译会把所在的绝对目录写进去，你的个人目录就会跟着 `seqtk.exe` 一起发出去。
即使去掉调试信息，`assert()` 仍会保留 `__FILE__`，这正是前缀映射要改写的内容。
编译脚本会在产物里仍能搜到源码目录或你的用户目录时直接报错。

### 为什么要加这个补丁

`seqtk.c` 在 `stk_randbase` 与 `stk_mergefa` 中调用了 `drand48()`、`srand48()`
和 `lrand48()`。MSVC/MinGW 的 C 运行库不提供它们，链接会报
`undefined reference to 'drand48'`。
`tools/seqtk-build/mingw_prng_shim.c` 按 Single UNIX Specification 实现了这个
48 位线性同余生成器，而不是把函数空实现掉，因此 `randbase` 和 `mergefa -r` 在
Windows 上依然可用。补丁只参与编译，上游源码一行未改。

如果你的工具链本身就提供这三个符号（部分 MSYS2 UCRT 构建会提供），把补丁从命令行
去掉即可。

## macOS 与 Linux

不需要补丁，POSIX 运行库已有 drand48 系列函数。

```bash
tools/seqtk-build/build_seqtk_macos.sh /path/to/seqtk-1.5     # 生成 bin/macos/seqtk
```

手工编译：

```bash
cc -O2 -Wall seqtk.c -o ../bin/macos/seqtk -lz
```

在 mac 上若链接器找不到 zlib，先 `brew install zlib` 再把头文件与库路径告诉编译器。

## 验证编译结果

仓库内的二进制带有指纹，便于与自行编译的结果比对：

```powershell
sha256sum bin\windows\seqtk.exe
# b844d8f0cee53681903f71848207d8ddace051d6aee51e79d1a49431bfe9846d
bin\windows\seqtk.exe                     # 标准错误输出 "Version: 1.5-r133"
bin\windows\seqtk.exe seq -A tests\fixtures\sample.fq
bin\windows\seqtk.exe randbase tests\fixtures\sample.fa   # 专门走补丁那条路径
python tools\probe_seqtk.py                # 一次性跑完全部子命令与选项
```

重新编译不要求逐字节复现该指纹——编译器版本、其构建配置以及 zlib 的构建方式都会
改变产物——所以请把它当作对所运行文件的完整性校验，并把上面几条命令作为确认自编译
产物行为一致的手段。随附的 `.exe` 以**静态**方式链接 zlib，这正是
[THIRD_PARTY_NOTICES.zh-CN.md](THIRD_PARTY_NOTICES.zh-CN.md) 需要列出 zlib 声明的原因。

**关于仓库内校验和的发布关卡。** 对外发布的二进制不得携带它被编译时所在的目录，
因此仓库内的 `bin/windows/seqtk.exe` 由 `tools\seqtk-build\build_seqtk_windows.bat`
产出：该脚本强制 `-g0` 与两条 `-ffile-prefix-map` 路径改写，并且在产物仍然指向构建机
本身时直接拒绝结束。这一要求用"统计检出目录所在盘符前缀的出现次数"来核验：下面两个
计数都必须是 `0`。把下面的 `D` 换成你的仓库所在盘符：

```bash
grep -a -o -F 'D:/' bin/windows/seqtk.exe | wc -l
grep -a -o -F 'D:\' bin/windows/seqtk.exe | wc -l
```

两个结果都必须是 `0`。只要有一个不是，就用
`tools\seqtk-build\build_seqtk_windows.bat` 重新编译——该脚本正是为此而强制 `-g0`
与前缀映射——随后把新的指纹写回本文与英文版。每次更换二进制都要重新审计一次。仓库内
这份文件已通过该关卡：产物为 246,433 字节，上面两个计数都是 `0`，且
`tools/probe_seqtk.py` 会对其跑完全部 82 项子命令/选项探针。重编译不会逐字节复现它，
所以校验和的作用是标识这份产物本身，而真正证明"重编译产物还是同一个程序"的是探针比对。

`python -m pytest tests -q` 会自动使用该程序；找不到时相关用例自动跳过。

## 许可证立场

seqtk 由其作者以 MIT 许可发布。编译出的 `seqtk.exe` 是 seqtk 的一份副本，而 MIT
要求版权声明与许可声明必须保留在*软件的所有副本*中——二进制副本同样算副本。这就是
`bin/windows/LICENSE.seqtk.txt` 与 `.exe` 并列存放的原因：它是上游 `LICENSE` 文件的
逐字节拷贝，使声明随二进制本身传播，而不只是随仓库传播。同样的文本也在本文所在仓库
的 [LICENSE.txt](../LICENSE.txt) 中逐字保留，打包流程会把它们一并放进
`dist/SeqTK-GUI.exe`。

`seqtk.c` 本身又 `#include` 了 `kseq.h` 与 `khash.h`，两者均由 Attractive Chaos 以
MIT 许可发布，且都被上游 `Makefile` 列为 `seqtk` 目标的前置依赖
（`seqtk:seqtk.c khash.h kseq.h`），因此同样作为一部分被编译进随附的二进制。它们的
声明紧挨 seqtk 的声明逐字收录在 [LICENSE.txt](../LICENSE.txt) 中，并在
[THIRD_PARTY_NOTICES.zh-CN.md](THIRD_PARTY_NOTICES.zh-CN.md) 里说明；两个头文件各自
的措辞并不相同，此处按各自原文保留而不做统一。

`seqtk_gui/` 下的界面代码是独立作品，由本项目贡献者以 MIT 许可发布，不链接 seqtk 的
任何代码，只是启动一个子进程。

由于编译时额外加入了 `mingw_prng_shim.c`，随附的二进制构成 seqtk 的**修改版本**。
MIT 并未规定标注义务，但 zlib 要求不得掩饰版本改动，而且面对一份别人无法阅读的
二进制，这两句说明值得写，因此该改动已在上文与
[THIRD_PARTY_NOTICES.zh-CN.md](THIRD_PARTY_NOTICES.zh-CN.md) 中记录。补丁文件本身
是本项目的原创作品，带有自己的 `SPDX-License-Identifier: MIT` 文件头；它不是上游代码，
也不会因此被置于 Heng Li 的版权之下。

本文所述内容都不是 seqtk 的官方发布，seqtk 一名只用于说明本界面驱动的对象，
见 [README.zh-CN.md](../README.zh-CN.md) 的免责声明。

如果你不希望把预编译二进制纳入 git，可以删除 `bin/windows/seqtk.exe`（以及
`bin/windows/LICENSE.seqtk.txt`），让使用者按本文自行编译，或通过
**工具 > 指定 seqtk 程序…** 指向自己已有的程序。
