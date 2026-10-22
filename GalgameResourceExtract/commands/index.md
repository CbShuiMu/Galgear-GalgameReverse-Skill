# 提取工具索引

所有程序路径相对于本技能目录解析，不依赖 Shell 的当前目录。以下工具均通过 CLI 调用，无需 GUI；Ethornell、Mangetsu、pfs-rs 和 CriCodecs 已提供 Windows x64 运行文件，无需现场编译或另装 Python。

| 工具 | 入口 | 提取时的适用范围与命令文档 |
| --- | --- | --- |
| GARbro CLI | `tools/GARbro-cli/GARbro.Console.exe` | 多引擎归档识别、列表与提取；见 [GARbro CLI](garbro.md) |
| Ethornell | `tools/ethornell/ethornell.exe` | BGI/Ethornell ARC20 原样提取及独立 DSC 解压、密钥读取；见 [Ethornell 命令](ethornell.md) |
| Mangetsu | `tools/mangetsu/*.exe` | Tsukihime Remake Switch 的 MRG/HED/NAM、MZP、MZX、NXX、HFA 及特定脚本文本表；见 [Mangetsu 命令](mangetsu.md) |
| pfs-rs | `tools/pfs-rs/pfs-rs.exe` | Artemis PF8/PFS 列表与提取；见 [pfs-rs 命令](pfs-rs.md) |
| CriCodecs | `tools/cricodecs.exe` | CRI CPK、AWB/ACB 等容器列表与提取，HCA/ADX/AHX 解码及 ACB 静态 cue 导出；见 [CriCodecs 命令](cricodecs.md) |

按文件头、引擎及版本证据选择工具，调用前阅读对应命令文档。GARbro 的 DLL、配置和 `GameData/`、Ethornell 的 `_internal/` 及各工具许可证须保持随包位置。解包与脚本解析是独立步骤；这些工具不会自动生成对白映射。Mangetsu 的条目索引、NAM 名称、扇区填充及额外压缩层需单独记录，不能把生成的提取文件名直接当成游戏中的语音引用。

使用 CriCodecs 时，先以 `INPUT -m --json` 和 `INPUT --list --raw --json` 检查格式与条目。重建基线使用容器的原样提取，解码 WAV 和 cue 渲染结果另存；CPK 中的脚本仍需单独解析。最终仅选中一个条目时，`-o` 是完整文件路径；按列表中的完整 `path` 为每条资源指定输出，避免扁平化或覆盖。ACB cue 计划索引、波形列表索引、AWB wave ID 与脚本引用须分别核对，不能假定一个波形等于一条对白或完整 cue。


GARbro 的资料覆盖与读取限制见 [常见引擎支持情况](../catalog/garbro-support.md)，不能据此承诺脚本解析或回写。
