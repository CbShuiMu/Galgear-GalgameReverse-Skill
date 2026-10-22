# 重建工具索引

随附路径应相对于本技能目录解析，不依赖 Shell 的当前目录。以下工具均通过 CLI 调用，无需 GUI；Ethornell、Mangetsu、pfs-rs 和 CriCodecs 已提供 Windows x64 运行文件，无需现场编译或另装 Python。

| 工具 | 入口 | 封包时的适用范围与命令文档 |
| --- | --- | --- |
| GARbro CLI | `tools/GARbro-cli/GARbro.Console.exe` | 通过 `f --writable` 确认的可写格式；见 [GARbro CLI](garbro.md) |
| Ethornell | `tools/ethornell/ethornell.exe` | BGI/Ethornell ARC20 创建及独立 DSC 压缩；见 [Ethornell 命令](ethornell.md) |
| Mangetsu | `tools/mangetsu/*.exe` | MRG/HED/NAM 重建、按索引替换，MZP 封装、MZX/NXGX 压缩及特定文本表回填；见 [Mangetsu 命令](mangetsu.md) |
| pfs-rs | `tools/pfs-rs/pfs-rs.exe` | Artemis PF8/PFS 创建；见 [pfs-rs 命令](pfs-rs.md) |
| CriCodecs | `tools/cricodecs.exe` | CRI CPK 等受支持容器创建/修改、AWB 按索引替换及 WAV→HCA/ADX/AHX 编码；见 [CriCodecs 命令](cricodecs.md) |

按文件头、引擎及版本证据选择工具，调用前阅读对应文档。Mangetsu 的 HFA 仅支持提取，不能据此承诺 HFA 重建。保持 GARbro 的 DLL/配置/`GameData/`、Ethornell 的 `_internal/` 及各工具许可证随包位置。缺少运行文件时报告具体缺项，不把已有预编译 CLI 的使用变成编译流程。

CriCodecs 不提供通用 ACB 创建或修改；AWB 替换后仍需核对 ACB 的引用和资源元数据。CPK 列表索引、CPK ID、AWB wave ID 不能互换。需要 HCA/ADX/AHX 时先准备采样率、声道和循环信息正确的 WAV，再编码为目标格式；不能仅重命名扩展名，也不能用有损编码前后 WAV 的哈希相等作为验收条件。

使用 GalTTS 输出或资源清单时，阅读[资源交接与重建](../guides/resource-workflow.md)。`scripts/resource_workflow.py init/merge` 使用 Python 标准库，可用于已确认路径的原样资源快照与合并；`pack/verify` 的归档后端仅为 GARbro，不能把其他程序传给 `--garbro`。选择其他 CLI 时，独立创建、重新提取并比对暂存清单中的资源。

