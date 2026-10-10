# seqtk 1.5-r133 子命令一览

界面提供的所有子命令与选项，全部逐条转录自上游 seqtk 1.5-r133 的 `seqtk.c`。由 `scripts/generate_commands_doc.py` 生成，请勿手工修改。

## 通用处理

### `seq`

FASTA/Q 通用转换

```text
seqtk seq [options] <in.fq>|<in.fa>
```

**选项**

| 标志 | 取值 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `-q` | int | `0` | 将质量值低于 INT 的碱基置为遮蔽 [0] |
| `-X` | int | `255` | 将质量值高于 INT 的碱基置为遮蔽 [255] |
| `-n` | char | `unset` | 被遮蔽的碱基替换为 CHAR；不设置则转为小写 |
| `-l` | int | `0` | 每行碱基数，0 表示 2^32-1（单行输出） [0] |
| `-Q` | int | `33` | 质量值偏移：ASCII-INT 得到碱基质量 [33] |
| `-s` | int | `11` | 随机种子（与 -f 同时生效） [11] |
| `-f` | float | `1.0` | 按比例 FLOAT 抽样序列 [1] |
| `-M` | file | `unset` | 按 BED 或名称列表 FILE 遮蔽区域 [空] |
| `-L` | int | `0` | 丢弃长度短于 INT 的序列 [0] |
| `-F` | char | `unset` | 伪造 FASTQ 质量串使用的字符 [未设置] |
| `-c` | 开关 | `off` | 遮蔽补集区域（与 -M 同时生效） |
| `-r` | 开关 | `off` | 反向互补 |
| `-R` | 开关 | `off` | 同时输出正向序列与反向互补 |
| `-A` | 开关 | `off` | 强制输出 FASTA（丢弃质量值，-a 等价） |
| `-C` | 开关 | `off` | 去掉行头中的注释 |
| `-N` | 开关 | `off` | 丢弃含歧义碱基的序列 |
| `-1` | 开关 | `off` | 仅输出第 2n-1 条 reads |
| `-2` | 开关 | `off` | 仅输出第 2n 条 reads |
| `-V` | 开关 | `off` | 按 '(-Q) - 33' 平移质量值 |
| `-U` | 开关 | `off` | 全部碱基转大写 |
| `-x` | 开关 | `off` | 所有小写碱基转换为 -n 指定的字符 |
| `-S` | 开关 | `off` | 去除序列中的空白字符 |

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `input` | `seq_file` | 必填 | <in.fq>\|<in.fa> |

**说明**: stk_seq 的 getopt 串接受 -a 并与 -A 走同一分支，但上游帮助文本从未列出 -a；界面统一暴露 -A。seqtk 本身接受单个 '-' 以读取标准输入，但界面始终传入文件路径。stk_seq 的帮助文本把 -n 描述为 “0 for lowercase [0]”，与代码不符：mask_chr 的初值是整数 0（即 NUL 字符），只有它非 0 时才用作遮蔽字符，否则把被遮蔽的碱基转为小写；显式传入 -n 0 会把数字 0 写进序列。因此规格不为 -n 设置默认值，用户在界面里填入字符后才下发该选项。-x 也只在 -n 给出非 0 字符时才会替换小写碱基。

### `size`

统计序列条数与碱基总数

```text
seqtk size <in.fq>|<in.fa>
```

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `input` | `seq_file` | 必填 | <in.fq>\|<in.fa> |

### `comp`

统计 FASTA/Q 的核苷酸组成

```text
seqtk comp [options] <in.fa>|<in.fq>
```

**选项**

| 标志 | 取值 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `-u` | 开关 | `off` | 仅统计大写碱基 |
| `-r` | file | `unset` | 仅统计 BED 文件 FILE 中的区域 |

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `input` | `seq_file` | 必填 | <in.fa>\|<in.fq> |

**说明**: 输出列：chr、length、#A、#C、#G、#T、#2、#3、#4、#CpG、#tv、#ts、#CpG-ts。使用 -r 时每行对应 BED 中的一个区域而非一条序列，行首多出 chr、beg、end 三列，共 14 列；上游帮助只描述了不带 -r 时的列布局。

### `sample`

对序列抽样

```text
seqtk sample [options] <in.fa>|<in.fq> <frac>|<number>（>=1 表示条数，<1 表示比例）
```

**选项**

| 标志 | 取值 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `-2` | 开关 | `off` | 两遍模式：慢一倍但内存占用显著降低 |
| `-s` | int | `11` | 随机种子 [11] |

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `input` | `seq_file` | 必填 | <in.fa>\|<in.fq> |
| `number` | `number` | 必填 | <frac>\|<number>（>=1 表示条数，<1 表示比例） |

**说明**: 双端数据需对两个文件使用相同的 -s 种子才能保持配对。-2 只在参数为整数时生效：传入比例时 stk_sample 仍走单遍路径并忽略该标志；两遍模式不接受标准输入。

### `subseq`

从 FASTA/Q 中提取子序列

```text
seqtk subseq [options] <in.fa>|<in.fq> <in.bed>|<name.list>
```

**选项**

| 标志 | 取值 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `-t` | 开关 | `off` | 以 TAB 分隔输出 |
| `-s` | 开关 | `off` | 识别链方向（读取 BED 第 6 链列） |
| `-l` | int | `0` | 输出每行长度 [0] |

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `input` | `seq_file` | 必填 | <in.fa>\|<in.fq> |
| `region` | `region_file` | 必填 | <in.bed>\|<name.list> |

**说明**: 若只需少量区域，建议改用 samtools faidx。

### `fqchk`

FASTQ 质控（碱基/质量汇总）

```text
seqtk fqchk [options] <in.fq>
```

**选项**

| 标志 | 取值 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `-q` | int | `20` | 质量阈值，-q0 输出全部质量值分布 [20] |

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `input` | `seq_file` | 必填 | <in.fq> |

### `mergepe`

将双端 FASTA/Q 交错合并

```text
seqtk mergepe <in1.fq> <in2.fq>
```

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `input1` | `seq_file` | 必填 | <in1.fq> |
| `input2` | `seq_file` | 必填 | <in2.fq> |

### `split`

将一个大文件拆分为多个小文件

```text
seqtk split [options] <prefix>（按 <prefix>.00001.fa、<prefix>.00002.fa … 命名写出） <in.fa>|<in.fq>
```

**选项**

| 标志 | 取值 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `-n` | int | `10` | 输出文件数量 [10] |
| `-l` | int | `0` | 每行长度 [0] |

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `prefix` | `out_prefix` | 必填 | <prefix>（按 <prefix>.00001.fa、<prefix>.00002.fa … 命名写出） |
| `input` | `seq_file` | 必填 | <in.fa>\|<in.fq> |

**说明**: split 自行写出文件，标准输出为空。界面会在所选工作目录下运行它。

### `trimfq`

使用 Phred 算法修剪 FASTQ

```text
seqtk trimfq [options] <in.fq>|<in.fa>
```

**选项**

| 标志 | 取值 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `-q` | float | `0.05` | 错误率阈值（被 -b/-e 覆盖） [0.05] |
| `-l` | int | `30` | 最多修剪至 INT bp（被 -b/-e 覆盖） [30] |
| `-b` | int | `0` | 从左端修剪 INT bp（非零则忽略 -q/-l） [0] |
| `-e` | int | `0` | 从右端修剪 INT bp（非零则忽略 -q/-l） [0] |
| `-L` | int | `-1` | 5' 端最多保留 INT bp；仅当取值 > 0 时才生效，并会忽略 -q/-l [-1] |

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `input` | `seq_file` | 必填 | <in.fq>\|<in.fa> |

**说明**: 上游帮助文本列出了 -Q（强制 FASTQ 输出），但 stk_trimfq 的 getopt 串 "l:q:b:e:L:" 并不接受它，因此界面不提供该选项。上游帮助把 -L 的默认值写成 [0]，而函数里 fixed_len 的初值是 -1；代码判据是 fixed_len > 0，两者行为相同，此处的默认值以代码初值 -1 为准。

## 区域分析

### `hety`

区域杂合度

```text
seqtk hety [options] <in.fa>
```

**选项**

| 标志 | 取值 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `-w` | int | `50000` | 窗口大小 [50000] |
| `-t` | int | `5` | 每个窗口的起始点数 [5] |
| `-m` | 开关 | `off` | 将小写视为已遮蔽 |

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `input` | `seq_file` | 必填 | <in.fa> |

### `gc`

识别高/低 GC 区域

```text
seqtk gc [options] <in.fa>
```

**选项**

| 标志 | 取值 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `-w` | 开关 | `off` | 识别高 AT 区域 |
| `-f` | float | `0.6` | 最小 GC 比例（配合 -w 时为 AT 比例） [0.60] |
| `-l` | int | `20` | 输出区域的最小长度 [20] |
| `-x` | float | `10.0` | X-dropoff 剪辑阈值 [10.0] |

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `input` | `seq_file` | 必填 | <in.fa> |

### `mutfa`

按指定位置对 FASTA 做点突变

```text
seqtk mutfa <in.fa> <in.snp>（至少四列：chr、1-based 位置、任意内容、替换后的碱基）
```

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `input` | `seq_file` | 必填 | <in.fa> |
| `snp` | `snp_file` | 必填 | <in.snp>（至少四列：chr、1-based 位置、任意内容、替换后的碱基） |

### `mergefa`

合并两个 FASTA/Q 文件

```text
seqtk mergefa [options] <in1.fa> <in2.fa>
```

**选项**

| 标志 | 取值 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `-q` | int | `0` | 质量阈值 [0] |
| `-i` | 开关 | `off` | 取交集 |
| `-m` | 开关 | `off` | 当任一位点为 N 时转为小写 |
| `-r` | 开关 | `off` | 从杂合位点中随机取一个等位 |
| `-h` | 开关 | `off` | 抑制输入中的杂合位点 |

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `input1` | `seq_file` | 必填 | <in1.fa> |
| `input2` | `seq_file` | 必填 | <in2.fa> |

**说明**: 合并后的序列输出到标准输出，(same,diff,hom-het,het-hom,het-het) 计数汇总输出到标准错误。-m 与 -i 不能同时使用：stk_mergefa 的判断条件是 is_mask && is_intersect，命中后直接退出，但它打印的报错文案把 -m 误写成了 -h，应以代码条件为准。

### `famask`

用 X 编码的 FASTA 遮蔽源 FASTA

```text
seqtk famask <src.fa> <mask.fa>
```

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `src` | `seq_file` | 必填 | <src.fa> |
| `mask` | `seq_file` | 必填 | <mask.fa> |

### `dropse`

从交错双端数据中丢弃未配对 reads

```text
seqtk dropse <in.fq>
```

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `input` | `seq_file` | 必填 | <in.fq> |

### `rename`

重命名序列名

```text
seqtk rename <in.fa>|<in.fq> [prefix]
```

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `input` | `seq_file` | 必填 | <in.fa>\|<in.fq> |
| `prefix` | `text` | 可选 | [prefix] |

### `randbase`

从杂合位点中随机选择一个碱基

```text
seqtk randbase <in.fa>
```

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `input` | `seq_file` | 必填 | <in.fa> |

### `cutN`

在长 N 区段处切割序列

```text
seqtk cutN [options] <in.fa>
```

**选项**

| 标志 | 取值 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `-n` | int | `1000` | N 区段最小长度 [1000] |
| `-p` | int | `10` | 非 N 碱基的罚分 [10] |
| `-g` | 开关 | `off` | 仅打印间隙，不输出序列 |

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `input` | `seq_file` | 必填 | <in.fa> |

### `gap`

获取间隙（非 ACGT 区段）位置

```text
seqtk gap [options] <in.fa>
```

**选项**

| 标志 | 取值 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `-l` | int | `50` | 间隙最小长度 [50] |

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `input` | `seq_file` | 必填 | <in.fa> |

### `listhet`

提取每个杂合位点的位置

```text
seqtk listhet <in.fa>
```

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `input` | `seq_file` | 必填 | <in.fa> |

### `hpc`

同源压缩序列

```text
seqtk hpc <in.fa>|<in.fq>
```

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `input` | `seq_file` | 必填 | <in.fa>\|<in.fq> |

### `telo`

在组装或长读长数据中识别端粒重复

```text
seqtk telo [options] <in.fa>|<in.fq>
```

**选项**

| 标志 | 取值 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `-m` | string | `CCCTAA` | 基序 [CCCTAA] |
| `-p` | int | `1` | 罚分 [1] |
| `-d` | int | `2000` | 最大下降值 [2000] |
| `-s` | int | `300` | 最小得分 [300] |
| `-P` | 开关 | `off` | 打印打分 |

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `input` | `seq_file` | 必填 | <in.fa>\|<in.fq> |

**说明**: 端粒区域以 BED 形式输出到标准输出；(端粒碱基数, 输入碱基数) 汇总输出到标准错误。stk_telo 会用断言校验 -m 基序的每个字符都必须对应 A/C/G/T，非法基序会使进程中止。加上 -P 后标准输出改为逐碱基的 P/Q 打分剖面，不再输出 BED 区域。

## 可由 `main()` 调用但未出现在 `seqtk` 帮助中

### `hrun` _(seqtk 帮助未列出)_

查找同源重复串（未出现在 seqtk 帮助列表中）

```text
seqtk hrun <in.fa>|<in.fq> [minLen]  默认 7
```

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `input` | `seq_file` | 必填 | <in.fa>\|<in.fq> |
| `min_len` | `number` | 可选 | [minLen]  默认 7 |

**说明**: stk_hrun 不解析任何选项，第二个位置参数为 minLen，默认 7。

### `kfreq` _(seqtk 帮助未列出)_

k-mer 频次统计（未出现在 seqtk 帮助列表中）

```text
seqtk kfreq <kmer>（如 ACGT，仅接受 A/C/G/T） <in.fa>
```

**位置参数**

| 参数 | 类型 | | 说明 |
| --- | --- | --- | --- |
| `kmer` | `kmer` | 必填 | <kmer>（如 ACGT，仅接受 A/C/G/T） |
| `input` | `seq_file` | 必填 | <in.fa> |

**说明**: stk_kfreq 会用断言校验每个字符必须是 A/C/G/T，非法 kmer 会使进程中止。

## 依据来源

已通过 `tests/test_seqtk_execution.py` 对 seqtk 1.5-r133 可执行文件逐条验证：每个子命令、每个选项都会真实执行一次。
