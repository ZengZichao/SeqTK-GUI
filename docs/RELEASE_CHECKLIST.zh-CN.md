# 发布前检查清单

以下都是第一次 `git push` 之前要完成的事。仓库**不会**替你初始化、提交或推送——
底部的命令请在你自己审阅过目录内容之后执行。

## 1. 验证代码

```powershell
python -m pytest tests -q                     # 全绿，且真实程序用例没有被跳过
python tools/probe_seqtk.py                   # 每个子命令 + 每个选项，退出码均为 0
python scripts/generate_commands_doc.py       # 运行后不应产生差异
python main.py                                # 真正启动一次
tools\build_exe_windows.bat                   # 生成单文件 exe
dist\SeqTK-GUI.exe                            # 打包版也要亲自启动一次
```

在运行中的界面里逐项确认：

* [ ] 真实的 FASTA 与 FASTQ 都能打开并转换
* [ ] `seq -A`、`sample`、`subseq`、`split`、`telo` 的结果符合预期
* [ ] **命令行** 标签页里的内容与你手敲的一致
* [ ] 故意填一个错误路径时，seqtk 的 `[E::…]` 出现在日志页而不是结果页
* [ ] 勾选 **将标准输出写入文件** 后，产物与终端里用 `>` 重定向的字节完全相同
* [ ] **视图 > 语言** 与 **视图 > 主题** 会改变包括表单在内的全部内容
* [ ] 重启程序后，语言、主题、上次命令与已填参数都被恢复
* [ ] 状态栏显示 seqtk 路径与 `1.5-r133`

## 2. 验证文档

* [ ] `README.md` 与 `README.zh-CN.md` 描述的功能范围一致
* [ ] 两个 README 里的每个链接都指向仓库内真实存在的文件
* [ ] `docs/` 下每个页面都有中英文两份
* [ ] 非官方声明同时出现在两个 README、关于对话框和 `LICENSE.txt` 中
* [ ] `LICENSE.txt` 同时包含本项目的 MIT 正文、逐字保留的 seqtk MIT 声明，以及
      `kseq.h` 与 `khash.h` 的 MIT 声明——`seqtk.c` 包含了这两个头文件，因此
      `bin/windows/seqtk.exe` 同样是它们的副本
* [ ] 上游的笔误仍然存在：`grep -c "20082-2012" LICENSE.txt
      docs/THIRD_PARTY_NOTICES.md docs/THIRD_PARTY_NOTICES.zh-CN.md` 三处都应命中——
      没有人"顺手"把它改对
* [ ] `bin/windows/LICENSE.seqtk.txt` 与上游 `LICENSE` 逐字节一致（用 `cmp` 与 seqtk
      源码树比对），使声明如 MIT 对每一副本所要求的那样随二进制一同传播
* [ ] 只要 `bin/windows/seqtk.exe` 仍在仓库里，`docs/THIRD_PARTY_NOTICES*.md` 中就
      不得出现"本项目不再分发 seqtk"的说法；两个 README 与 `LICENSE.txt` 里也不行
* [ ] 本项目自己的版权行写明的是你愿意公开的权利人。这里刻意采用
      `Copyright (c) <年份> SeqTK-GUI contributors`：它既满足 MIT 对"版权声明人"的要求，
      又不暴露真实姓名或个人邮箱。上游那行 `Heng Li <lh3@me.com>` 必须保留——那是 seqtk
      的声明而非你的，MIT 要求你逐字复制。若你希望署名，请使用稳定的公开标识（GitHub
      登录名）而不是邮箱，并在同一次提交里同步更新 `LICENSE.txt`、`CONTRIBUTING*.md`
      以及所有 `SPDX-License-Identifier` 文件头
* [ ] 截图与当前界面一致：`python scripts/make_screenshots.py`
* [ ] 逐张打开四张图，读一遍路径栏：这里按设计显示占位路径 `C:\seqtk-demo\...`，
      绝不是你实际工作的目录

## 3. 确认没有多余文件被纳入版本管理

```powershell
git init -b main
git add -A
git status --short            # 逐行检查这个列表
```

应当包含：源码、测试、测试数据、文档、截图、`LICENSE.txt`、`README*.md`、
`CONTRIBUTING*.md`、`requirements.txt`、`pyproject.toml`、`.gitignore`、
`.gitattributes`、`packaging/`（含 `packaging/licenses/`）、`tools/`，以及
`bin/windows/seqtk.exe` 与 `bin/windows/LICENSE.seqtk.txt`。

不应出现：`__pycache__/`、`.pytest_cache/`、`build/`、`dist/`、`docs/screenshots/`
下生成的 `*.ini`、任何个人路径、任何真实数据集。`build/SeqTK-GUI/*.toc` 会记录构建机
上的绝对路径（形如盘符加 `Users` 的个人目录），这也是 `build/` 必须保持被忽略的
另一个原因。

对外发布的二进制本身也要过同一道检查，因为带 `-g` 的编译会把所在目录写进可执行文件。
把下面的 `D` 换成你的仓库所在盘符：

```bash
grep -a -o -F 'D:/' bin/windows/seqtk.exe | wc -l
grep -a -o -F 'D:\' bin/windows/seqtk.exe | wc -l
```

两个结果都必须是 `0`。只要有一个不是，就按
[docs/BUILD_SEQTK.zh-CN.md](BUILD_SEQTK.zh-CN.md) 重新编译 `seqtk.exe`——该命令强制
`-g0` 与 `-ffile-prefix-map` 路径改写，且脚本在产物仍含本机目录时会直接报错——然后
更新其中记录的校验和。注意：只检查 `C:\Users` 是不够的——仓库若放在用户目录之外，
泄漏的就是它自己所在盘符的路径；而目录名含非 ASCII 字符时，逐字节比对也会失效，
这正是检查必须依据构建路径本身来做的原因。工具链自身的路径（例如编译器的构建目录）
不属于个人数据，可以保留。

`bin/windows/seqtk.exe` 是唯一一个仍可能带上构建路径的受版本管理文件，因为编译器会
把它写进去。在项目根目录检查一次：

```powershell
Select-String -Path bin\windows\seqtk.exe -Pattern (Get-Location).Path -SimpleMatch -Quiet
```

期望结果是 `False`。若是 `True`，说明它是在开着调试信息的情况下编译的，发布前用
`tools\seqtk-build\build_seqtk_windows.bat` 重新编译——该脚本会传 `-g0` 与前缀映射。

`bin/windows/seqtk.exe`（246 KB，为了让克隆后开箱即用而特意纳入版本管理）需要你明确
表态：若不想提交二进制，删掉它（连同 `bin/windows/LICENSE.seqtk.txt`），让使用者按
[docs/BUILD_SEQTK.zh-CN.md](BUILD_SEQTK.zh-CN.md) 自行编译，见该文档最后一节。无论
选择哪条路线，`packaging/licenses/` 中的许可文本与被打包的 `LICENSE.seqtk.txt` 只在
仍然随仓库分发二进制时才是必需的。

另外，本机 git 未配置全局身份，提交前先设置：

```powershell
git config user.name "Your Name"
git config user.email "you@example.com"
```

## 4. 提交并打标签

```powershell
git commit -m "Add an unofficial PySide6 front end for seqtk 1.5-r133"
git tag -a v1.0.0 -m "First public release"
```

## 5. 发布（由你执行）

在 GitHub 上创建仓库时**不要**初始化 README/.gitignore，然后：

```powershell
git remote add origin https://github.com/<owner>/seqtk-gui.git
git push -u origin main --follow-tags
```

仓库建立后建议：

* About 填：`Unofficial GUI front end for seqtk (PySide6). Not affiliated with seqtk.`
* Website 指向 `README.md`
* License：GitHub 会从 `LICENSE.txt` 自动识别为 MIT
* 若有协作者，给 `main` 加分支保护
* 暂时不需要 `SECURITY.md`；安全问题先用 GitHub 的私密 issue 报告

## 6. 发布之后

* 在 GitHub 上确认 README 渲染正常，两张截图与双语文档表格都能显示。
* 在干净的克隆目录再跑一次测试，排查被 `.gitignore` 误伤的文件。
* 把 `dist/SeqTK-GUI.exe`（约 48 MB）作为 tag 的 **Releases** 附件上传——它就是给没有
  Python 的用户的单文件下载包。不要提交进仓库：`dist/` 已被忽略，这么大的二进制不该进
  git 历史。
* 打包版首次启动需要几秒解压到临时目录；如果用户遇到 SmartScreen 或杀毒软件告警，考虑给
  exe 做代码签名。
