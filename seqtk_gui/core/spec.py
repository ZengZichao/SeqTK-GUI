"""Every seqtk subcommand and option, transcribed from upstream source.

Source of truth: ``seqtk.c`` from lh3/seqtk 1.5-r133. Each option below comes
from the ``getopt()`` optstring of the matching ``stk_*`` handler, and each
default comes from the variable initialisation in that handler. Nothing here
is guessed. When the upstream usage text and the code disagree, the code wins
and the mismatch is recorded in ``Command.notes``.

This module is pure data and imports no Qt, so the tests and the documentation
generator can use it without a display.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

SEQTK_VERSION = "1.5-r133"

# Positional argument kinds: they drive the widget and the file dialog.
KIND_SEQ = "seq_file"          # FASTA/Q input, may be .gz
KIND_REGION = "region_file"    # BED or name list
KIND_SNP = "snp_file"          # chr pos any base-to
KIND_NUMBER = "number"         # sample fraction or read count
KIND_KMER = "kmer"             # A/C/G/T string
KIND_PREFIX = "out_prefix"     # split writes <prefix>.00001.fa ...
KIND_TEXT = "text"             # free-form string (rename prefix)

FILE_FILTER_SEQ = "Sequence files (*.fa *.fasta *.fn *.in *.fq *.fastq *.qf *.fq.gz *.fa.gz *.fasta.gz);;All files (*)"
FILE_FILTER_TABLE = "Table files (*.bed *.txt *.list *.tsv);;All files (*)"


@dataclass(frozen=True)
class Option:
    """A single getopt option of one subcommand."""

    flag: str
    value_kind: Optional[str] = None  # None -> boolean flag
    default: Any = None
    help_en: str = ""
    help_zh: str = ""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    file_filter: Optional[str] = None
    max_length: int = 0  # for char options: how many characters the CLI uses

    @property
    def is_flag(self) -> bool:
        return self.value_kind is None


@dataclass(frozen=True)
class Positional:
    key: str
    kind: str
    required: bool = True
    help_en: str = ""
    help_zh: str = ""
    file_filter: Optional[str] = None
    default: Any = None


@dataclass(frozen=True)
class Command:
    name: str
    group: str
    summary_en: str
    summary_zh: str
    options: Sequence[Option] = field(default_factory=tuple)
    positionals: Sequence[Positional] = field(default_factory=tuple)
    # The subcommand writes files itself and prints nothing useful.
    writes_files_itself: bool = False
    documented: bool = True
    notes_en: str = ""
    notes_zh: str = ""

    @property
    def flags(self) -> Sequence[Option]:
        return tuple(o for o in self.options if o.is_flag)

    @property
    def valued(self) -> Sequence[Option]:
        return tuple(o for o in self.options if not o.is_flag)


# ---------------------------------------------------------------------------
# seq - common transformation of FASTA/Q
# getopt: "N12q:l:Q:aACrn:s:f:M:L:cVUX:SF:xR"
# ---------------------------------------------------------------------------
_SEQ = Command(
    name="seq",
    group="general",
    summary_en="common transformation of FASTA/Q",
    summary_zh="FASTA/Q 通用转换",
    options=(
        Option("q", "int", 0, "-q INT    mask bases with quality lower than INT [0]",
               "-q INT    将质量值低于 INT 的碱基置为遮蔽 [0]", min_value=0, max_value=93),
        Option("X", "int", 255, "-X INT    mask bases with quality higher than INT [255]",
               "-X INT    将质量值高于 INT 的碱基置为遮蔽 [255]", min_value=0, max_value=255),
        Option("n", "char", None, "-n CHAR   masked bases converted to CHAR; leave unset to lowercase",
               "-n CHAR   被遮蔽的碱基替换为 CHAR；不设置则转为小写", max_length=1),
        Option("l", "int", 0, "-l INT    number of residues per line; 0 for 2^32-1 [0]",
               "-l INT    每行碱基数，0 表示 2^32-1（单行输出） [0]", min_value=0),
        Option("Q", "int", 33, "-Q INT    quality shift: ASCII-INT gives base quality [33]",
               "-Q INT    质量值偏移：ASCII-INT 得到碱基质量 [33]", min_value=0, max_value=126),
        Option("s", "int", 11, "-s INT    random seed (effective with -f) [11]",
               "-s INT    随机种子（与 -f 同时生效） [11]"),
        Option("f", "float", 1.0, "-f FLOAT  sample FLOAT fraction of sequences [1]",
               "-f FLOAT  按比例 FLOAT 抽样序列 [1]", min_value=0.0, max_value=1.0),
        Option("M", "file", None, "-M FILE   mask regions in BED or name list FILE [null]",
               "-M FILE   按 BED 或名称列表 FILE 遮蔽区域 [空]", file_filter=FILE_FILTER_TABLE),
        Option("L", "int", 0, "-L INT    drop sequences with length shorter than INT [0]",
               "-L INT    丢弃长度短于 INT 的序列 [0]", min_value=0),
        Option("F", "char", None, "-F CHAR   fake FASTQ quality [unset]",
               "-F CHAR   伪造 FASTQ 质量串使用的字符 [未设置]", max_length=1),
        Option("c", None, False, "-c        mask complement region (effective with -M)",
               "-c        遮蔽补集区域（与 -M 同时生效）"),
        Option("r", None, False, "-r        reverse complement", "-r        反向互补"),
        Option("R", None, False, "-R        output both forward and reverse complement",
               "-R        同时输出正向序列与反向互补"),
        Option("A", None, False, "-A        force FASTA output (discard quality)  (-a is a synonym)",
               "-A        强制输出 FASTA（丢弃质量值，-a 等价）"),
        Option("C", None, False, "-C        drop comments at the header lines",
               "-C        去掉行头中的注释"),
        Option("N", None, False, "-N        drop sequences containing ambiguous bases",
               "-N        丢弃含歧义碱基的序列"),
        Option("1", None, False, "-1        output the 2n-1 reads only", "-1        仅输出第 2n-1 条 reads"),
        Option("2", None, False, "-2        output the 2n reads only", "-2        仅输出第 2n 条 reads"),
        Option("V", None, False, "-V        shift quality by '(-Q) - 33'",
               "-V        按 '(-Q) - 33' 平移质量值"),
        Option("U", None, False, "-U        convert all bases to uppercases", "-U        全部碱基转大写"),
        Option("x", None, False, "-x        convert all lowercases to -n",
               "-x        所有小写碱基转换为 -n 指定的字符"),
        Option("S", None, False, "-S        strip of white spaces in sequences",
               "-S        去除序列中的空白字符"),
    ),
    positionals=(Positional("input", KIND_SEQ, True,
                           "<in.fq>|<in.fa>", "<in.fq>|<in.fa>"),),
    notes_en="stk_seq's getopt string accepts '-a' and routes it to the same case as '-A', while the "
             "usage text never lists '-a'; the GUI exposes '-A'. "
             "seqtk accepts a lone '-' to read stdin, but the GUI always passes a file path. "
             "The usage text of stk_seq describes '-n CHAR' as '0 for lowercase [0]', which "
             "the code contradicts: mask_chr is initialised to the integer 0 (the NUL "
             "character) and is only used as the mask when it is non-zero, otherwise the "
             "masked base is lowercased. Passing '-n 0' therefore writes the digit 0 into "
             "the sequence, so this spec gives -n no default and leaves the option out until "
             "the user types a character. '-x' likewise only rewrites lowercase bases when "
             "-n supplies a non-zero character.",
    notes_zh="stk_seq 的 getopt 串接受 -a 并与 -A 走同一分支，但上游帮助文本从未列出 -a；界面统一暴露 -A。"
             "seqtk 本身接受单个 '-' 以读取标准输入，但界面始终传入文件路径。"
             "stk_seq 的帮助文本把 -n 描述为 “0 for lowercase [0]”，与代码不符：mask_chr 的初值是整数 0（即 NUL 字符），"
             "只有它非 0 时才用作遮蔽字符，否则把被遮蔽的碱基转为小写；显式传入 -n 0 会把数字 0 写进序列。"
             "因此规格不为 -n 设置默认值，用户在界面里填入字符后才下发该选项。"
             "-x 也只在 -n 给出非 0 字符时才会替换小写碱基。",
)

_SIZE = Command(
    name="size",
    group="general",
    summary_en="report the number sequences and bases",
    summary_zh="统计序列条数与碱基总数",
    options=(),
    positionals=(Positional("input", KIND_SEQ, True, "<in.fq>|<in.fa>", "<in.fq>|<in.fa>"),),
)

_COMP = Command(
    name="comp",
    group="general",
    summary_en="get the nucleotide composition of FASTA/Q",
    summary_zh="统计 FASTA/Q 的核苷酸组成",
    options=(
        Option("u", None, False, "-u  only count uppercased bases", "-u  仅统计大写碱基"),
        Option("r", "file", None, "-r FILE  restrict counts to regions in BED FILE",
               "-r FILE  仅统计 BED 文件 FILE 中的区域", file_filter=FILE_FILTER_TABLE),
    ),
    positionals=(Positional("input", KIND_SEQ, True, "<in.fa>|<in.fq>", "<in.fa>|<in.fq>"),),
    notes_en="Output columns: chr, length, #A, #C, #G, #T, #2, #3, #4, #CpG, #tv, #ts, #CpG-ts. "
             "With -r each row describes one BED region rather than one sequence and starts with "
             "chr, beg and end, giving fourteen columns; the upstream usage text only documents "
             "the layout without -r.",
    notes_zh="输出列：chr、length、#A、#C、#G、#T、#2、#3、#4、#CpG、#tv、#ts、#CpG-ts。"
             "使用 -r 时每行对应 BED 中的一个区域而非一条序列，行首多出 chr、beg、end 三列，共 14 列；"
             "上游帮助只描述了不带 -r 时的列布局。",
)

_SAMPLE = Command(
    name="sample",
    group="general",
    summary_en="subsample sequences",
    summary_zh="对序列抽样",
    options=(
        Option("2", None, False, "-2  2-pass mode: twice as slow but with much reduced memory",
               "-2  两遍模式：慢一倍但内存占用显著降低"),
        Option("s", "int", 11, "-s INT  RNG seed [11]", "-s INT  随机种子 [11]"),
    ),
    positionals=(
        Positional("input", KIND_SEQ, True, "<in.fa>|<in.fq>", "<in.fa>|<in.fq>"),
        Positional("number", KIND_NUMBER, True,
                   "<frac>|<number>  values >= 1 are read counts, below 1 are fractions",
                   "<frac>|<number>（>=1 表示条数，<1 表示比例）"),
    ),
    notes_en="For paired-end data sample both files with the same -s seed to keep pairs together. "
             "-2 only applies to a whole-number argument: with a fraction stk_sample keeps the "
             "one-pass path and ignores the flag, and two-pass mode refuses to read stdin.",
    notes_zh="双端数据需对两个文件使用相同的 -s 种子才能保持配对。"
             "-2 只在参数为整数时生效：传入比例时 stk_sample 仍走单遍路径并忽略该标志；两遍模式不接受标准输入。",
)

_SUBSEQ = Command(
    name="subseq",
    group="general",
    summary_en="extract subsequences from FASTA/Q",
    summary_zh="从 FASTA/Q 中提取子序列",
    options=(
        Option("t", None, False, "-t  TAB delimited output", "-t  以 TAB 分隔输出"),
        Option("s", None, False, "-s  strand aware (reads the BED strand column)",
               "-s  识别链方向（读取 BED 第 6 链列）"),
        Option("l", "int", 0, "-l INT  sequence line length [0]", "-l INT  输出每行长度 [0]", min_value=0),
    ),
    positionals=(
        Positional("input", KIND_SEQ, True, "<in.fa>|<in.fq>", "<in.fa>|<in.fq>"),
        Positional("region", KIND_REGION, True, "<in.bed>|<name.list>", "<in.bed>|<name.list>"),
    ),
    notes_en="Use 'samtools faidx' instead when only a few regions are intended.",
    notes_zh="若只需少量区域，建议改用 samtools faidx。",
)

_FQCHK = Command(
    name="fqchk",
    group="general",
    summary_en="fastq QC (base/quality summary)",
    summary_zh="FASTQ 质控（碱基/质量汇总）",
    options=(
        Option("q", "int", 20, "-q INT  quality threshold; use -q0 for the full distribution [20]",
               "-q INT  质量阈值，-q0 输出全部质量值分布 [20]", min_value=0, max_value=93),
    ),
    positionals=(Positional("input", KIND_SEQ, True, "<in.fq>", "<in.fq>"),),
)

_MERGEPE = Command(
    name="mergepe",
    group="general",
    summary_en="interleave two PE FASTA/Q files",
    summary_zh="将双端 FASTA/Q 交错合并",
    options=(),
    positionals=(
        Positional("input1", KIND_SEQ, True, "<in1.fq>", "<in1.fq>"),
        Positional("input2", KIND_SEQ, True, "<in2.fq>", "<in2.fq>"),
    ),
)

_SPLIT = Command(
    name="split",
    group="general",
    summary_en="split one file into multiple smaller files",
    summary_zh="将一个大文件拆分为多个小文件",
    writes_files_itself=True,
    options=(
        Option("n", "int", 10, "-n INT  number of files [10]", "-n INT  输出文件数量 [10]", min_value=1),
        Option("l", "int", 0, "-l INT  line length [0]", "-l INT  每行长度 [0]", min_value=0),
    ),
    positionals=(
        Positional("prefix", KIND_PREFIX, True,
                   "<prefix>  files are written as <prefix>.00001.fa, <prefix>.00002.fa ...",
                   "<prefix>（按 <prefix>.00001.fa、<prefix>.00002.fa … 命名写出）"),
        Positional("input", KIND_SEQ, True, "<in.fa>|<in.fq>", "<in.fa>|<in.fq>"),
    ),
    notes_en="split writes files itself; nothing goes to stdout. The GUI runs it in the chosen working directory.",
    notes_zh="split 自行写出文件，标准输出为空。界面会在所选工作目录下运行它。",
)

_TRIMFQ = Command(
    name="trimfq",
    group="general",
    summary_en="trim FASTQ using the Phred algorithm",
    summary_zh="使用 Phred 算法修剪 FASTQ",
    options=(
        Option("q", "float", 0.05, "-q FLOAT  error rate threshold (disabled by -b/-e) [0.05]",
               "-q FLOAT  错误率阈值（被 -b/-e 覆盖） [0.05]", min_value=0.0, max_value=1.0),
        Option("l", "int", 30, "-l INT  maximally trim down to INT bp (disabled by -b/-e) [30]",
               "-l INT  最多修剪至 INT bp（被 -b/-e 覆盖） [30]", min_value=0),
        Option("b", "int", 0, "-b INT  trim INT bp from left (non-zero to disable -q/-l) [0]",
               "-b INT  从左端修剪 INT bp（非零则忽略 -q/-l） [0]"),
        Option("e", "int", 0, "-e INT  trim INT bp from right (non-zero to disable -q/-l) [0]",
               "-e INT  从右端修剪 INT bp（非零则忽略 -q/-l） [0]"),
        Option("L", "int", -1, "-L INT  retain at most INT bp from the 5'-end; only a value > 0 takes "
                                "effect and it then disables -q/-l [-1]",
               "-L INT  5' 端最多保留 INT bp；仅当取值 > 0 时才生效，并会忽略 -q/-l [-1]"),
    ),
    positionals=(Positional("input", KIND_SEQ, True, "<in.fq>|<in.fa>", "<in.fq>|<in.fa>"),),
    notes_en="Upstream usage text lists '-Q  force FASTQ output', but the getopt string of stk_trimfq "
             "(\"l:q:b:e:L:\") does not accept it, so the option is not exposed here. "
             "The usage text also prints '-L INT ... [0]' while the handler initialises fixed_len "
             "to -1; the code tests fixed_len > 0, so -1 and 0 behave alike and the default "
             "recorded here follows the code.",
    notes_zh="上游帮助文本列出了 -Q（强制 FASTQ 输出），但 stk_trimfq 的 getopt 串 \"l:q:b:e:L:\" 并不接受它，"
             "因此界面不提供该选项。上游帮助把 -L 的默认值写成 [0]，而函数里 fixed_len 的初值是 -1；"
             "代码判据是 fixed_len > 0，两者行为相同，此处的默认值以代码初值 -1 为准。",
)

_HETY = Command(
    name="hety",
    group="regional",
    summary_en="regional heterozygosity",
    summary_zh="区域杂合度",
    options=(
        Option("w", "int", 50000, "-w INT  window size [50000]", "-w INT  窗口大小 [50000]", min_value=1),
        Option("t", "int", 5, "-t INT  # start positions in a window [5]", "-t INT  每个窗口的起始点数 [5]", min_value=1),
        Option("m", None, False, "-m  treat lowercases as masked", "-m  将小写视为已遮蔽"),
    ),
    positionals=(Positional("input", KIND_SEQ, True, "<in.fa>", "<in.fa>"),),
)

_GC = Command(
    name="gc",
    group="regional",
    summary_en="identify high- or low-GC regions",
    summary_zh="识别高/低 GC 区域",
    options=(
        Option("w", None, False, "-w  identify high-AT regions", "-w  识别高 AT 区域"),
        Option("f", "float", 0.6, "-f FLOAT  min GC fraction (or AT fraction for -w) [0.60]",
               "-f FLOAT  最小 GC 比例（配合 -w 时为 AT 比例） [0.60]", min_value=0.0, max_value=1.0),
        Option("l", "int", 20, "-l INT  min region length to output [20]", "-l INT  输出区域的最小长度 [20]", min_value=1),
        Option("x", "float", 10.0, "-x FLOAT  X-dropoff [10.0]",
               "-x FLOAT  X-dropoff 剪辑阈值 [10.0]", min_value=0.0),
    ),
    positionals=(Positional("input", KIND_SEQ, True, "<in.fa>", "<in.fa>"),),
)

_MUTFA = Command(
    name="mutfa",
    group="regional",
    summary_en="point mutate FASTA at specified positions",
    summary_zh="按指定位置对 FASTA 做点突变",
    options=(),
    positionals=(
        Positional("input", KIND_SEQ, True, "<in.fa>", "<in.fa>"),
        Positional("snp", KIND_SNP, True,
                    "<in.snp>  at least four columns: chr  1-based-pos  any  base-changed-to",
                    "<in.snp>（至少四列：chr、1-based 位置、任意内容、替换后的碱基）"),
    ),
)

_MERGEFA = Command(
    name="mergefa",
    group="regional",
    summary_en="merge two FASTA/Q files",
    summary_zh="合并两个 FASTA/Q 文件",
    options=(
        Option("q", "int", 0, "-q INT  quality threshold [0]", "-q INT  质量阈值 [0]", min_value=0),
        Option("i", None, False, "-i  take intersection", "-i  取交集"),
        Option("m", None, False, "-m  convert to lowercase when one of the input base is N",
               "-m  当任一位点为 N 时转为小写"),
        Option("r", None, False, "-r  pick a random allele from het", "-r  从杂合位点中随机取一个等位"),
        Option("h", None, False, "-h  suppress hets in the input", "-h  抑制输入中的杂合位点"),
    ),
    positionals=(
        Positional("input1", KIND_SEQ, True, "<in1.fa>", "<in1.fa>"),
        Positional("input2", KIND_SEQ, True, "<in2.fa>", "<in2.fa>"),
    ),
    notes_en="The merged sequences go to stdout; the (same,diff,hom-het,het-hom,het-het) counters go to stderr. "
             "-m and -i cannot be applied at the same time: stk_mergefa tests is_mask && is_intersect and "
             "exits, but the message it prints names '-h' instead of '-m', so trust the condition in the "
             "code rather than the wording of the error.",
    notes_zh="合并后的序列输出到标准输出，(same,diff,hom-het,het-hom,het-het) 计数汇总输出到标准错误。"
             "-m 与 -i 不能同时使用：stk_mergefa 的判断条件是 is_mask && is_intersect，命中后直接退出，"
             "但它打印的报错文案把 -m 误写成了 -h，应以代码条件为准。",
)

_FAMASK = Command(
    name="famask",
    group="regional",
    summary_en="apply a X-coded FASTA to a source FASTA",
    summary_zh="用 X 编码的 FASTA 遮蔽源 FASTA",
    options=(),
    positionals=(
        Positional("src", KIND_SEQ, True, "<src.fa>", "<src.fa>"),
        Positional("mask", KIND_SEQ, True, "<mask.fa>", "<mask.fa>"),
    ),
)

_DROPSE = Command(
    name="dropse",
    group="regional",
    summary_en="drop unpaired from interleaved PE FASTA/Q",
    summary_zh="从交错双端数据中丢弃未配对 reads",
    options=(),
    positionals=(Positional("input", KIND_SEQ, True, "<in.fq>", "<in.fq>"),),
)

_RENAME = Command(
    name="rename",
    group="regional",
    summary_en="rename sequence names",
    summary_zh="重命名序列名",
    options=(),
    positionals=(
        Positional("input", KIND_SEQ, True, "<in.fa>|<in.fq>", "<in.fa>|<in.fq>"),
        Positional("prefix", KIND_TEXT, False, "[prefix]", "[prefix]"),
    ),
)

_RANDBASE = Command(
    name="randbase",
    group="regional",
    summary_en="choose a random base from hets",
    summary_zh="从杂合位点中随机选择一个碱基",
    options=(),
    positionals=(Positional("input", KIND_SEQ, True, "<in.fa>", "<in.fa>"),),
)

_CUTN = Command(
    name="cutN",
    group="regional",
    summary_en="cut sequence at long N",
    summary_zh="在长 N 区段处切割序列",
    options=(
        Option("n", "int", 1000, "-n INT  min size of N tract [1000]", "-n INT  N 区段最小长度 [1000]", min_value=1),
        Option("p", "int", 10, "-p INT  penalty for a non-N [10]", "-p INT  非 N 碱基的罚分 [10]", min_value=0),
        Option("g", None, False, "-g  print gaps only, no sequence", "-g  仅打印间隙，不输出序列"),
    ),
    positionals=(Positional("input", KIND_SEQ, True, "<in.fa>", "<in.fa>"),),
)

_GAP = Command(
    name="gap",
    group="regional",
    summary_en="get the gap locations",
    summary_zh="获取间隙（非 ACGT 区段）位置",
    options=(
        Option("l", "int", 50, "-l INT  min size of a gap [50]", "-l INT  间隙最小长度 [50]", min_value=1),
    ),
    positionals=(Positional("input", KIND_SEQ, True, "<in.fa>", "<in.fa>"),),
)

_LISTHET = Command(
    name="listhet",
    group="regional",
    summary_en="extract the position of each het",
    summary_zh="提取每个杂合位点的位置",
    options=(),
    positionals=(Positional("input", KIND_SEQ, True, "<in.fa>", "<in.fa>"),),
)

_HPC = Command(
    name="hpc",
    group="regional",
    summary_en="homopolymer-compressed sequence",
    summary_zh="同源压缩序列",
    options=(),
    positionals=(Positional("input", KIND_SEQ, True, "<in.fa>|<in.fq>", "<in.fa>|<in.fq>"),),
)

_TELO = Command(
    name="telo",
    group="regional",
    summary_en="identify telomere repeats in asm or long reads",
    summary_zh="在组装或长读长数据中识别端粒重复",
    options=(
        Option("m", "string", "CCCTAA", "-m STR  motif [CCCTAA]", "-m STR  基序 [CCCTAA]",
               max_length=15),
        Option("p", "int", 1, "-p INT  penalty [1]", "-p INT  罚分 [1]"),
        Option("d", "int", 2000, "-d INT  max drop [2000]", "-d INT  最大下降值 [2000]", min_value=1),
        Option("s", "int", 300, "-s INT  min score [300]", "-s INT  最小得分 [300]", min_value=1),
        Option("P", None, False, "-P  print scoring", "-P  打印打分"),
    ),
    positionals=(Positional("input", KIND_SEQ, True, "<in.fa>|<in.fq>", "<in.fa>|<in.fq>"),),
    notes_en="telomere regions go to stdout as BED; the (telo_bases, input_bases) summary goes to stderr. "
             "stk_telo asserts that every character of the -m motif maps to A/C/G/T, so an invalid motif "
             "aborts the process. -P switches stdout from BED regions to the per-base P/Q scoring profile.",
    notes_zh="端粒区域以 BED 形式输出到标准输出；(端粒碱基数, 输入碱基数) 汇总输出到标准错误。"
             "stk_telo 会用断言校验 -m 基序的每个字符都必须对应 A/C/G/T，非法基序会使进程中止。"
             "加上 -P 后标准输出改为逐碱基的 P/Q 打分剖面，不再输出 BED 区域。",
)

_HRUN = Command(
    name="hrun",
    group="undocumented",
    summary_en="find homopolymer runs (not listed by 'seqtk' usage)",
    summary_zh="查找同源重复串（未出现在 seqtk 帮助列表中）",
    documented=False,
    options=(),
    positionals=(
        Positional("input", KIND_SEQ, True, "<in.fa>|<in.fq>", "<in.fa>|<in.fq>"),
        Positional("min_len", KIND_NUMBER, False, "[minLen]  default 7", "[minLen]  默认 7"),
    ),
    notes_en="stk_hrun takes no getopt options; the second positional is minLen, default 7.",
    notes_zh="stk_hrun 不解析任何选项，第二个位置参数为 minLen，默认 7。",
)

_KFREQ = Command(
    name="kfreq",
    group="undocumented",
    summary_en="k-mer frequencies (not listed by 'seqtk' usage)",
    summary_zh="k-mer 频次统计（未出现在 seqtk 帮助列表中）",
    documented=False,
    options=(),
    positionals=(
        Positional("kmer", KIND_KMER, True, "<kmer>  e.g. ACGT; only A/C/G/T accepted",
                   "<kmer>（如 ACGT，仅接受 A/C/G/T）"),
        Positional("input", KIND_SEQ, True, "<in.fa>", "<in.fa>"),
    ),
    notes_en="stk_kfreq asserts every character is A/C/G/T, so an invalid k-mer aborts the process.",
    notes_zh="stk_kfreq 会用断言校验每个字符必须是 A/C/G/T，非法 kmer 会使进程中止。",
)

COMMANDS: tuple[Command, ...] = (
    _SEQ, _SIZE, _COMP, _SAMPLE, _SUBSEQ, _FQCHK, _MERGEPE, _SPLIT, _TRIMFQ,
    _HETY, _GC, _MUTFA, _MERGEFA, _FAMASK, _DROPSE, _RENAME, _RANDBASE,
    _CUTN, _GAP, _LISTHET, _HPC, _TELO, _HRUN, _KFREQ,
)

COMMANDS_BY_NAME: dict[str, Command] = {c.name: c for c in COMMANDS}

GROUPS = ("general", "regional", "undocumented")
GROUP_LABELS_EN = {"general": "General", "regional": "Regional analysis",
                   "undocumented": "Undocumented"}
GROUP_LABELS_ZH = {"general": "通用处理", "regional": "区域分析", "undocumented": "未公开列出"}


def get_command(name: str) -> Command:
    return COMMANDS_BY_NAME[name]
