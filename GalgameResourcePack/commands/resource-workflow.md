# 资源辅助命令

入口为相对于本技能根目录的 `scripts/resource_workflow.py`，需要 Python 3.10+ 和标准库。`init` 可为各类原样资源建立快照；当前 `merge` 读取 GalTTS 专用映射和审计字段，不能直接接收任意替换目录。清单规则见[资源清单契约](../contracts/resource-manifest.md)，接收 GalTTS 输出的操作顺序见[资源交接流程](../guides/resource-workflow.md)。

`init/merge` 可处理其他 CLI 准备且已确认路径的原样资源；`pack/verify` 仅调用随附 GARbro，不能把其他程序传给 `--garbro`。使用其他 CLI 时按[归档重建流程](../guides/packing.md)独立创建、原样提取并比对暂存清单。

## 参数与调用

| 命令 | 必需参数 | 用途 |
| --- | --- | --- |
| `init` | `--original-root`、`--archive`、`--format`、`--manifest` | 建立原始资源与归档身份快照。对已确认的创建设置重复使用 `-O` / `--option Name=Value` |
| `merge` | `--manifest`、`--replacements`、`--staging`、`--output` | 验证身份并合并到新目录。默认 `--mode full`；`--mode patch` 仅包含选定的替换条目 |
| `pack` | `--manifest`、`--garbro`、`--output`、`--verification-dir`、`--report` | 检查暂存目录，使用记录的设置创建归档，并执行提取与哈希校验 |
| `verify` | `--manifest`、`--garbro`、`--archive`、`--verification-dir`、`--report` | 在新提取目录中，依据暂存清单验证现有归档 |

将示例变量解析为真实路径。`$workflow` 为本技能的辅助脚本，`$garbro` 为随附 `tools/GARbro-cli/GARbro.Console.exe`，`$python` 为 Python 3.10+ 解释器。先按所选工具的命令文档原样提取；GARbro 不使用会转换资源的 `-ca` 或 `-if`，输出到新目录。

```powershell
# 对原样资源目录建立快照；格式与必需选项须有原始归档证据。
& $python $workflow init --original-root $originalRoot --archive $originalArchive --format XP3 -O Version=2 -O RetainDirs=true --manifest $originalManifest

# 另行完成 GalTTS 配置、生成和当前 handoff 审计后，传入其 .galtts/resources.json。
& $python $workflow merge --manifest $originalManifest --replacements $replacementManifest --staging $stagingRoot --output $stagedManifest

# 创建新归档，重新打开并原样提取，比较每个预期资源的哈希。
& $python $workflow pack --manifest $stagedManifest --garbro $garbro --output $outputArchive --verification-dir $verificationRoot --report $verificationReport
```

`$replacementManifest` 为 TTS 输出目录中的 `.galtts/resources.json`。每个进程成功退出后再继续。上述命令不解析对白、翻译文本、启动未经请求的后台任务或安装结果。

## 输出、拒绝条件与验证范围

- 所有输出归档、清单、报告文件以及暂存、验证目录都必须是新的，不修改资源输入。建立快照前必须确认原样提取完整；`init` 只记录调用方选定的格式与选项，不恢复加密方案或版本。
- `merge` 拒绝不完整、缺失、过期、未映射或已改变的替换资源，也拒绝目录链接及忽略大小写后的资源冲突。完整模式保留每个未修改资源，包括非音频文件；不会从生成目录复制 `.galtts` 元数据。补丁模式不能证明游戏支持补丁。
- `pack` 先验证暂存哈希，再按清单记录的格式与选项创建归档；`pack/verify` 比较原样提取后精确解码出的资源字节。仅大小写变化的名称规范化会被报告，其他写入器特定资源变换导致比对失败，由 AI 助手按格式分析，不静默接受。
- 验证失败时保留生成归档供检查，并返回非零退出码。报告包含缺失、意外出现和已改变的路径、数量、归档哈希及 `game_playback: not_tested`。
- 辅助脚本及其集成测试均不自动实施引擎级内存检查。音频长度与边界按[专项检查](../guides/resource-workflow.md#解码长度与越界预防)执行；游戏内运行是否完成单独报告。维护测试命令见本技能的 [AGENTS.md](../AGENTS.md#维护与验证)。
