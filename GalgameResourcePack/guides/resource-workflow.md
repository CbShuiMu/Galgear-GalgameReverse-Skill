# 资源交接与归档重建

`scripts/resource_workflow.py` 串联归档原样提取、GalTTS 输出、暂存、归档创建与哈希校验。它使用 Python 3.10+ 和标准库。对白解析和资源匹配仍由 AI 助手负责。

`init/merge` 可用于由其他 CLI 准备、已确认路径的原样资源；`pack/verify` 仅调用 GARbro，不支持通用命令后端，不能把 Ethornell、Mangetsu、pfs-rs 或 CriCodecs 传给 `--garbro`。选择这些工具时，阅读 [Ethornell](../commands/ethornell.md)、[Mangetsu](../commands/mangetsu.md)、[pfs-rs](../commands/pfs-rs.md) 或 [CriCodecs](../commands/cricodecs.md) 命令文档，由 AI 助手独立封包、重新提取并按暂存清单验证。多层封装、MRG 条目索引和填充需按格式规则核对，不能仅比较生成的提取文件名。

## 资源根目录与清单

每个原始归档使用独立的原样资源根目录。将 GalTTS 的 `asset_root` 设置为该目录。映射路径是归档内部路径，而非相对于游戏安装目录的路径。例如，归档包含 `char_a/001.ogg` 时，映射必须使用 `char_a/001.ogg`，不要人为添加 `Voice/` 前缀。映射、清单、生成输出、暂存与验证目录都应放在原样资源目录之外。

所有交接清单使用 `kind: gal-resource-manifest`、`schema_version: 1`、`stage`、`complete` 标记及 `entries` 数组。条目的 `path` 使用 `/` 分隔符，标识原始归档资源。路径必须是相对路径，不得向上穿越父目录，并且忽略大小写后仍须唯一。

| 阶段 | 生成方 | 内容 |
| --- | --- | --- |
| `extracted` | `resource_workflow.py init` | 所有原始资源及其源路径、大小、SHA-256，原始归档身份信息，目标格式及显式创建选项 |
| `generated` | `galtts.py handoff` 或通过的完整 `audit` | 选定替换资源、原始与生成文件身份信息、映射身份信息、生成指纹与根目录 |
| `staged` | `resource_workflow.py merge` | 预期的完整或补丁资源集、保留或替换操作、预期哈希、暂存根目录与输入清单身份信息 |

生成阶段的 `resources.json` 保存在 TTS 输出的 `.galtts/` 目录下。只接受 `complete: true` 的清单。合并前立即运行 `handoff` 审计当前配置，此操作不加载模型。相对路径布局与旧版扁平布局的 TTS 输出都携带原始条目路径，因此合并脚本无需根据基本文件名猜测即可恢复目录。

## 解码长度与越界预防

收到 TTS 资源时核对生成审计与目标引擎验证的范围。`resources.json` 的 `complete: true` 表示生成批次审计完整；`resource_workflow.py` 的暂存与归档哈希比对表示资源字节一致。二者均不会自动验证游戏解码器的内存边界。

1. **确认字段和解码规则。** 根据目标游戏的实际格式、引擎版本与解码器，区分压缩数据长度、每声道采样帧数、交错 PCM 字节数和容器头尾开销，确定哪些字段控制分配容量。FFmpeg 与游戏可能因编码延迟、首尾裁剪、填充或块边界处理不同而输出不同数据量；不能直接将 FFmpeg 输出的 PCM 大小当作游戏所需长度。元数据换算公式必须有目标引擎的验证依据。
2. **按最终资源重新填写长度。** 压缩长度按实际封装载荷计算，解码长度按经过目标引擎自身或匹配解码器验证的口径计算，并按该格式规则填写头部及相关长度字段。不要沿用原音频的旧长度、用时长或码率估算，或将某次故障的“加 256 字节”推广到其他资源。头部长度错误应修正字段，不要随意裁剪音频来迎合错误值。
3. **封包前核对边界。** 逐条检查替换资源的声明长度、块与偏移边界、采样率、声道、位深、对齐、格式校验信息和字段整数范围。以原始资源作对照，在隔离进程中使用保护页、哨兵或可用内存检测工具检查目标解码器是否越界读写，覆盖短/长音频、编码块边界和保留的非语言音频。实际写入必须落在引擎真实分配范围内。设置超时；越界、崩溃、异常退出、超时或缺少完整结果都判为失败。
4. **封包后复核实际字节。** 对最终归档原样提取的资源重复长度与边界检查，确认测试的是最终安装候选。若 Pack 转码或重新封装改变了 TTS 输出，记录新的资源哈希、长度与验证证据，并重新建立受影响的暂存/验证清单；不能沿用旧字节的通过结论。资源或解码器版本变化后也要重验。
5. **分别报告验证结果。** 项目报告记录资源与解码器的 SHA-256（或可辨识版本）、检查方法、覆盖数量、声明和实测长度，以及结构、引擎边界和游戏播放各项状态。无法运行目标解码器时明确写“引擎解码边界未验证”，不能将成功播放、普通解码或归档哈希一致写成越界检查通过。已知长度不一致或越界未修正前停止安装。

以上要求由 AI 助手按目标游戏执行，适用于随附流程和自定义封包器；当前 `pack`、`verify` 及集成测试不自动实施引擎级内存检查。游戏专用的字段偏移、采样换算和函数地址需要重新确认，不能跨游戏套用。

## 命令

将示例变量解析为真实路径。`$workflow` 是本技能的 `scripts/resource_workflow.py`；`$tts` 是 GalTTS 的 `scripts/galtts.py`；`$garbro` 是随附可执行文件。TTS 使用所选模型环境的 Python，资源辅助脚本可使用任意 Python 3.10+ 解释器。示例中两者均用 `$python` 表示。

```powershell
# 原样提取，不使用 -ca 或 -if。使用新目录。
& $garbro x -q -s -o $originalRoot $originalArchive

# 对原样资源目录建立快照，提供已识别的格式和必需选项。
& $python $workflow init --original-root $originalRoot --archive $originalArchive --format XP3 -O Version=2 -O RetainDirs=true --manifest $originalManifest

# Agent 生成对白映射；照常通过 GalTTS 配置并生成。
# 新 TTS 项目默认使用相对路径布局。改变布局时使用新的输出目录。
& $python $tts --project game configure --input-json $mapping --asset-root $originalRoot --output-dir $generatedRoot --profile $profile --output-layout relative
& $python $tts --project game plan
& $python $tts --project game run
& $python $tts --project game handoff

# 将全部未修改资源与已验证替换资源合并到新的暂存目录。
& $python $workflow merge --manifest $originalManifest --replacements $replacementManifest --staging $stagingRoot --output $stagedManifest

# 封包，重新打开并提取，比较每个预期资源的哈希。
& $python $workflow pack --manifest $stagedManifest --garbro $garbro --output $outputArchive --verification-dir $verificationRoot --report $verificationReport
```

`$replacementManifest` 为 `$generatedRoot/.galtts/resources.json`。继续之前检查每个退出码。此处的命令均不会解析对白、翻译文本、启动未经请求的后台任务，或将结果安装到游戏中。

| 命令 | 必需参数 | 用途 |
| --- | --- | --- |
| `init` | `--original-root`、`--archive`、`--format`、`--manifest` | 建立原始资源与归档身份快照。对已确认的创建设置重复使用 `-O` / `--option Name=Value` |
| `merge` | `--manifest`、`--replacements`、`--staging`、`--output` | 验证身份并合并到新目录。默认 `--mode full`；`--mode patch` 仅包含选定的替换条目 |
| `pack` | `--manifest`、`--garbro`、`--output`、`--verification-dir`、`--report` | 检查暂存目录，使用记录的设置创建归档，并执行提取与哈希校验 |
| `verify` | `--manifest`、`--garbro`、`--archive`、`--verification-dir`、`--report` | 在新提取目录中，依据暂存清单验证现有归档 |

所有输出清单、报告文件以及暂存、验证目录都必须是新的。不会修改资源输入。合并前会拒绝不完整、缺失、过期、未映射或已改变的替换资源，也会拒绝目录链接及忽略大小写后的资源冲突。完整模式保留每个未修改资源，包括非音频文件；不会从生成目录复制 `.galtts` 元数据。

辅助脚本比较原样提取后精确解码出的资源字节。仅大小写变化的名称规范化会被报告。其他写入器特定资源变换会导致比对失败，需要 AI 助手按格式明确分析，不会被静默接受。验证失败会保留生成归档供检查，并返回非零退出码。报告包含缺失、意外出现和已改变的路径、数量、归档哈希及 `game_playback: not_tested`。需要时仍须进行游戏内播放检查。

辅助脚本不会恢复加密方案或版本，补丁模式也不能证明游戏支持补丁。`init` 记录 AI 助手选定的格式与选项；AI 助手必须确定它们与原始归档的兼容性。快照只覆盖提交给它的原样资源目录，因此建立快照前必须检查提取是否完整。

## 集成检查

```powershell
& $python <GalPack>/scripts/test_resource_workflow.py --ffmpeg <FFmpeg> --garbro <GARbro.Console.exe>
```

使用具有 GalTTS 批处理依赖的 Python 环境。测试在临时目录使用合成音频和模拟后端，验证 ZIP 和 XP3 提取、嵌套同名文件、生成、完整与补丁合并、归档往返、哈希失败及路径拒绝。不加载真实 TTS 模型，也不测试游戏内播放。
