# 参与贡献

感谢关注。这是一个非官方界面，因此判断贡献是否合格的标准是：**忠于 seqtk，并且中英文、
两种主题始终同步。**

## 基本规则

1. **计算全部交给 seqtk。** 不要用 Python 实现序列解析、转换或统计。界面缺什么，
   通常意味着上游缺什么。
2. **规格只是转录。** `seqtk_gui/core/spec.py` 里的选项、取值类型与默认值必须来自
   目标版本的 `seqtk.c`，见
   [docs/DEVELOPMENT.zh-CN.md](docs/DEVELOPMENT.zh-CN.md#唯一的重要规则)。
   上游 `getopt()` 不接受的标志一律不加，即使帮助文本里写了；把这种矛盾记在该命令的
   `notes_*` 字段里。
3. **双语才算完成。** 每一条界面文字都要有中英文，每一篇文档也要有两个语言版本。
4. **仓库里不留历史痕迹。** 注释与文档只描述当前设计，不写“原先”“本次修复”，不放
   变更记录文件，也不引用问题编号。
5. **以 MIT 进、以 MIT 出。** 提交贡献即表示同意按本项目许可发布。
6. **许可只在根目录声明一次。** 仓库**不**逐文件添加 SPDX 或版权文件头：
   `LICENSE.txt` 覆盖所有文件，而给 30 个文件盖上同样的头只是会在第一次改名时就
   过期的噪音。只有两个文件是有意保留的例外，因为根目录的 `LICENSE.txt` 对它们的
   覆盖方式与对 Python 包的覆盖方式不同：`bin/windows/seqtk.exe` 会单独流转，
   `tools/seqtk-build/mingw_prng_shim.c` 则在 Python 包之外参与编译，可能被人脱离
   仓库单独拷进自己的构建里。标识在这两处确实提供了额外信息，所以保留；其余文件
   照旧，除非你新增的文件也会以同样方式脱离本仓库流转。
   本项目自己的版权行是 `Copyright (c) <年份> SeqTK-GUI contributors`。这个措辞是
   刻意为之：MIT 需要一个版权声明人，而集体指称既满足这一要求，又不必把一个真实
   姓名或私人邮箱写进一份所有下游副本都必须逐字复制的文件。上游那行
   `Heng Li <lh3@me.com>` 性质不同——那是 MIT 要求我们逐字保留的 seqtk 声明，
   不得"顺手清理"、匿名化或修正，包括其中那个笔误。

## 环境准备

```bash
git clone <你的 fork>
cd seqtk-gui
python -m venv .venv
.venv\Scripts\activate          # Windows（macOS/Linux 用 source .venv/bin/activate）
python -m pip install -r requirements.txt
python main.py
```

日常开发大多不需要 seqtk 程序，相关测试会自动跳过。需要跑完整测试时，按
[docs/BUILD_SEQTK.zh-CN.md](docs/BUILD_SEQTK.zh-CN.md) 编译一个。

## 流程

1. 从 `main` 切出分支。
2. 完成修改。
3. 改了规格：运行 `python scripts/generate_commands_doc.py`。
4. 改了界面文案：**同时**更新 `seqtk_gui/i18n/strings/` 下的两个 JSON。
5. 运行 `python -m pytest tests -q`。
6. 手工启动一次，在两种语言、两种主题下检查受影响界面——静态检查发现不了被裁切的布局。
7. 提交 PR，说明用户可见的行为变化，涉及界面时附截图。

## 可以从这些地方入手

* 修正 `strings_zh.json` / `strings_en.json` 的措辞或翻译。
* 给 [docs/USER_GUIDE.zh-CN.md](docs/USER_GUIDE.zh-CN.md) 补充示例。
* 补齐 `core/paths.py` 的平台分支（macOS 支持已预留但未实装）。
* 修真实缺陷：先跑 `python tools/probe_seqtk.py`，它会用你的程序把每个子命令、每个
  选项都执行一遍。

## 报告问题

请附上：状态栏显示的 seqtk 版本、**命令行** 标签页里的完整命令、日志页内容、操作系统，
以及输入文件的样例（几条记录即可，不要上传真实数据）。

## 代码风格

Python 3.10 以上、4 空格缩进、每行约 100 列、公开函数写类型标注。界面用代码构建而不
是 `.ui` 文件，这样表单才能由规格自动生成。除非标准库确实无法满足需求，否则不新增依赖。
