# 重建工具索引

所有工具路径相对于本技能目录解析，不依赖 Shell 的当前目录；运行入口按 `tools/<工具>/` 分类，CLI 无需 GUI。rpatool、RLdev SEEN 与 Majiro 适配需要 Python 3.9+ 标准库；其余随附入口为 Windows 程序，GalArc 与 FreeMote 需要 .NET Framework 4.8。依赖、许可证和对应源码保持随包位置。

| 工具 | 入口 | 封包时的适用范围与命令文档 |
| --- | --- | --- |
| GARbro CLI | `tools/GARbro-cli/GARbro.Console.exe` | 通过 `f --writable` 确认的可写格式；见 [GARbro CLI](garbro.md) |
| Ethornell | `tools/ethornell/ethornell.exe` | BGI/Ethornell ARC20 创建及独立 DSC 压缩；见 [Ethornell 命令](ethornell.md) |
| Mangetsu | `tools/mangetsu/*.exe` | MRG/HED/NAM 重建、按索引替换，MZP 封装、MZX/NXGX 压缩及特定文本表回填；见 [Mangetsu 命令](mangetsu.md) |
| pfs-rs | `tools/pfs-rs/pfs-rs.exe` | Artemis PF8 创建，PF6 不提供原格式写入；见 [pfs-rs 命令](pfs-rs.md) |
| CriCodecs | `tools/cricodecs/cricodecs.exe` | CRI CPK 等受支持容器创建/修改、AWB 按索引替换及 WAV→HCA/ADX/AHX 编码；见 [CriCodecs 命令](cricodecs.md) |
| GalArc CLI 子集 | `tools/galarc-cli/galarc.exe` | 标准 NS2 创建；显式 `--raw` 创建新 Raw 平面 NOA，不能替代压缩/加密变体；见 [GalArc 命令](galarc.md) |
| FreeMote CLI | `tools/freemote/PsBuild.exe` | 支持的 PSB / SCN 从 JSON 与原样资源重建、内置 MDF 包装；见 [FreeMote 命令](freemote.md) |
| Siglus CLI | `tools/siglus-ssu/siglus-ssu.exe` | `pack --base` 保留已支持 PCK 的包级元数据并替换场景 DAT；见 [Siglus 命令](siglus-ssu.md) |
| rpatool CLI | `tools/rpatool/rpatool.py` | 创建标准 RPA v2 / v3，保留完整资源相对路径；见 [rpatool 命令](rpatool.md) |
| RLdev SEEN CLI | `tools/rldev-seen/rlseen.py` | 根据原生槽号重建 RealLive SEEN.TXT 原样成员归档；见 [SEEN 命令](rldev-seen.md) |
| Majiro V3 CLI | `tools/majiro-cli/majiro_cli.py` | 创建含有效 CRC-64 哈希的 ARC V3，仅接受小写 CP932 平面名称；见 [Majiro 命令](majiro-cli.md) |

按文件头、引擎及版本证据选择工具，调用前阅读对应文档。Mangetsu 的 HFA 仅支持提取，不能据此承诺 HFA 重建。保持 GARbro 的 DLL/配置/`GameData/`、Ethornell 的 `_internal/` 及各工具许可证随包位置。缺少运行文件时报告具体缺项，不把已有预编译 CLI 的使用变成编译流程。

CriCodecs 不提供通用 ACB 创建或修改；AWB 替换后仍需核对 ACB 的引用和资源元数据。CPK 列表索引、CPK ID、AWB wave ID 不能互换。需要 HCA/ADX/AHX 时先准备采样率、声道和循环信息正确的 WAV，再编码为目标格式；不能仅重命名扩展名，也不能用有损编码前后 WAV 的哈希相等作为验收条件。

使用 GalTTS 输出或资源清单时，阅读[资源交接与重建](../guides/resource-workflow.md)。`scripts/resource_workflow.py init/merge` 使用 Python 标准库，可用于已确认路径的原样资源快照与合并；`pack/verify` 的归档后端仅为 GARbro，不能把其他程序传给 `--garbro`。选择其他 CLI 时，独立创建、重新提取并比对暂存清单中的资源。

