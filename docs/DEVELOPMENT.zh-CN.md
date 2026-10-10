# 开发说明

## 架构

```
main.py
  -> seqtk_gui/app.py            QApplication、设置、语言、主题
       -> ui/main_window.py      组装各部分
            ui/command_list.py   24 个子命令，分组 + 可搜索
            ui/param_panel.py    由 core/spec.py 生成的表单
            ui/output_panel.py   标准输出 / 标准错误 / 命令行 三个标签页
            ui/themes.py         明亮与黑暗调色板、样式表
            ui/about_dialog.py   非官方声明、许可证正文
                 |
                 v
            core/cli_build.py    规格 + 表单值 -> argv、校验
            core/runner.py       QProcess：流式读取、标准输出可直接落盘
            core/binary_locator.py  定位 seqtk 并读取其自报版本
            core/paths.py        分平台路径
            core/settings.py     偏好持久化
            i18n/catalog.py      JSON 文案与运行时语言切换
```

依赖方向是单向的：`core` 不引入任何 Qt 控件（只用 `QtCore`），`i18n` 不引入 `ui`，
只有 `ui` 层接触控件。`core/spec.py` 除标准库外什么都不导入，因此测试和文档生成器
无需显示器即可使用它。

## 唯一的重要规则

`seqtk_gui/core/spec.py` 是对 `seqtk.c` 的转录，不是可以自由发挥的设计文档。
每个选项、取值类型与默认值都必须来自上游源码：

* 选项集合来自对应 `stk_*` 函数里的 `getopt(argc, argv, "...")`；
* 是否需要取值来自字母后是否有 `:`；
* 默认值来自该函数开头的变量初始化；
* 位置参数顺序来自该函数对 `argv[optind]` 的索引方式。

`tests/test_spec_against_source.py` 会用一份 getopt 字符串副本复核选项集合，
`tests/test_seqtk_execution.py` 会用真实程序把每个选项都跑一遍。上游增删标志位时，
两者都会失败。

### 修改或新增选项

1. 阅读 `seqtk.c` 中对应的 `stk_*` 函数。
2. 修改 `spec.py` 的 `Option`/`Positional`，保持中英双语文案。
3. 运行 `python scripts/generate_commands_doc.py`（命令表是生成的，漏跑会被
   `tests/test_docs_are_generated.py` 判失败）。
4. 运行 `python -m pytest tests -q`；有可执行文件时再跑 `python tools/probe_seqtk.py`。

## 表单值的语义

带取值的选项在未勾选时存为 `None`，勾选后才是具体值。`cli_build.build_argv` 会完全
跳过 `None`，因此界面绝不会替用户传他并没有要的开关，seqtk 的默认值始终是权威。
位置参数按规格顺序以字符串传入。

每个子命令的表单状态以 `form/<命令>/<键>` 字符串保存，带取值的选项编码为
`"是否启用|值"`，见 `SettingsStore.save_form`。

## 输出处理

`SeqtkRunner` 使用通道分离的 `QProcess` 并发化解码后的数据块，有两种模式：

* 预览 - 数据块进入标准输出标签页，受 `MAX_PREVIEW_CHARS` 限制；
* 重定向 - 调用 `setStandardOutputFile()` 把文件句柄直接交给子进程，数据完全不经过
  Python，等价于命令行的 `>`。

解码统一用 UTF-8 且 `errors="replace"`：seqtk 输出 ASCII，这样个别异常字节也不会
中断读取。

## 国际化

界面文案全部在 `i18n/strings/strings_zh.json` 与 `strings_en.json`。键使用点号分组：
`menu.`、`act.`、`panel.`、`field.`、`status.`、`validate.`、`dialog.`、`run.`、
`output.`、`tab.`、`about.`、`usage.`、`theme.`、`msg.`。

* 新键必须**同时**加到两个文件；`tests/test_i18n_completeness.py` 会比对键集合、
  拒绝空值、检查 `{占位符}` 是否一致，并扫描源码里 `tr("…")` 用到的键是否存在。
* `Language.pick(en, zh)` 用于放在规格数据里而非文案表里的文本，也就是上游帮助措辞
  及其译文。
* 需要跟随语言变化的控件会把一个取文本的函数登记到 `ParamPanel._retranslate`，
  由 `retranslate()` 统一重放。

## 主题

`ui/themes.py` 把 `light` 与 `dark` 各表示为一份颜色字典、一个 `QPalette` 构造器和
一段样式表。`apply_theme()` 同时固定 Fusion 风格，以便两个平台都能按调色板渲染。
新增颜色请改字典，不要在控件里写死字面量。

## 测试

```bash
python -m pytest tests -q                        # 全部
python -m pytest tests -q --ignore=tests/test_seqtk_execution.py   # 无需 seqtk 程序
python tools/probe_seqtk.py [path\to\seqtk.exe]  # 手工遍历全部选项
```

要点：

* 界面测试在 `QT_QPA_PLATFORM=offscreen` 下运行，并使用临时 `QSettings` 文件，
  不会污染真实配置。
* `tests/conftest.py` 会替换模态对话框；否则离屏运行时 `QMessageBox` 会永久阻塞。
* 测试里启动子进程后要用 `wait_for(app, predicate)` 推动事件循环——只调用
  `processEvents()` 的空转循环会瞬间返回，子进程来不及被回收。
* 找不到 seqtk 程序时，真实执行类用例会自动跳过。

## 打包

```powershell
tools\build_exe_windows.bat
```

脚本会在缺少 PyInstaller 时自动安装，并执行 `packaging/SeqTK-GUI.spec`，产出
**单个自包含的 `dist/SeqTK-GUI.exe`**。spec 以数据形式打进两样东西：

* `seqtk_gui/i18n/strings/*.json`——界面文案；
* `bin/<platform>/seqtk[.exe]`——界面要执行的原生程序。

启动时 PyInstaller 会把它们解压到 `sys._MEIPASS`，而
`core/paths.py::bundled_binary_candidates()` 查找该目录的顺序排在 exe 同级目录之前，
因此程序无需任何用户配置就能用自己那份 seqtk。查找顺序（含冻结模式）由
`tests/test_binary_lookup.py` 锁定。

设置 `ONEFILE=0` 可改为目录版：启动更快、也更不容易被杀毒软件误报，代价是要分发多个文件。

不用测试框架也能验证产物：启动 `dist/SeqTK-GUI.exe`，确认窗口标题为
`SeqTK-GUI (…) - seqtk 1.5-r133`，并在其运行期间查看
`%TEMP%\_MEI*\bin\windows\seqtk.exe` 是否存在——那正是被解压出来使用的那份；状态栏也会显示
解析到的路径。

macOS 上同样方式打包，再把结果包成 `.app`，并把 seqtk 放在 `Contents/MacOS` 或
`Contents/Resources` 下，解析逻辑依旧能找到它。

## 迁移到其他操作系统

代码里没有 Windows 专有实现。新增平台只需：

1. `core/paths.py`：在 `PLATFORM_DIRS` 中登记 `sys.platform`，并补配置目录分支。
2. `core/binary_locator.py`：`executable_name()` 在非 Windows 下已返回 `seqtk`。
3. `tools/seqtk-build/`：补一个编译脚本；MinGW 的 PRNG 补丁仅 Windows 需要。
4. 把程序放进 `bin/<platform>/` 并跑测试：真实执行用例通过同一个解析器就能用上它。

## 约定

* 注释只描述当前的设计与约束——不写历史、不写“原先/本次修改”、不引用任务编号。
* 不留死常量、无用样式和不可达分支，仓库以可直接公开的状态提交。
* 内容型文本左对齐，状态、提示与空态文案居中。
* 强调色背景上的文字一律为白色。
* 引用 seqtk 帮助原文时保持逐字，便于与上游 grep 对照。
