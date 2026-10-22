# 项目记忆

使用记忆在不同对话之间保留已验证的发现和工作检查点。这是一份显式的本地记录，不会自动存储全部对话或模型推理，也不会自行运行提取工具或恢复任务。

## 位置与首次使用

运行 `scripts/memory.py memory --where` 查找当前用户的状态。Windows 默认位置为 `%LOCALAPPDATA%/GalExtract/memory.json`。其他系统使用 `$XDG_STATE_HOME/gal-extract/memory.json`，未设置时回退到 `~/.local/state/gal-extract/memory.json`。`GAL_EXTRACT_HOME` 可覆盖状态目录；全局参数 `--memory FILE` 可显式指定文件。相关命令应保持相同的状态选择。

随包分发的 `memory.example.json` 有意保持为空。读取不存在的状态时返回空配置，不会写入文件。不会为用户预选游戏、引擎、提取工具、目录或硬件。真实路径、游戏细节与工作历史应保存在可分发技能之外。

## 记录内容

每个游戏安装或有实质差异的游戏版本建立一个项目。项目中的实用字段包括：

- `game_root` 和 `output_dir`：用户选定的绝对路径。
- `engine`：名称、置信度、证据及已知版本。保留不确定性，不要把推测记为事实。
- `resources`：已定位的归档、脚本、图像、音频、视频及其他目标资源路径，文件命名约定、格式或编码及相关资源 ID。
- `tools`：成功使用过的提取工具名称、版本、可执行文件路径与相关参数。命令参数保存为数组，避免凭据或 Shell 字符串。记忆不会执行存储的命令。
- `artifacts`：原样资源根目录、资源清单、按需解码或解析的结果；需要对白与语音关联时再记录映射 JSON 及相关语言或翻译状态。记录对白是原文还是经过核实的中文；字段名本身不能证明已翻译。
- `counts`：按目标资源类别实际测量的条目、成功、失败和重复数量；做过对白与语音关联时再记录已关联与未关联数量。
- `unresolved`：歧义、失败尝试及具体原因，以及下一项有效操作。不要存储完整对白、音频或私有推理。
- `sources`：已观察的相关源文件快照。元数据检查成本较低；可选 SHA-256 为选定文件提供更强的身份校验。
- `checkpoints`：阶段、状态、简短事实说明和已验证的产物路径。可按任务使用 `identify_engine`、`locate_resources`、`extract_resources`、`decode_resources`、`extract_text` 等阶段；`extract_voice`、`match` 和 `export_json` 只用于相关语音或关联任务。

在取得重要发现、完成阶段、发生失败或用户要求停止后更新。工作未通过相关检查时，不要将阶段标记为完成。检查点记录的是工作状态，不是执行其他工作的许可。

## 命令

使用可用的 Python 3 解释器；辅助脚本只依赖标准库。将占位符替换为实际路径。全局参数 `--memory` 和 `--project` 应放在子命令之前。

```powershell
& <PYTHON> <SKILL>/scripts/memory.py memory --where
& <PYTHON> <SKILL>/scripts/memory.py memory
& <PYTHON> <SKILL>/scripts/memory.py --project game configure --game-root D:/Games/Example --output-dir D:/Exports/Example
& <PYTHON> <SKILL>/scripts/memory.py --project game update --patch <FINDINGS_JSON>
& <PYTHON> <SKILL>/scripts/memory.py --project game observe --source D:/Games/Example/data.arc
& <PYTHON> <SKILL>/scripts/memory.py --project game checkpoint extract_resources --status completed --artifact D:/Exports/Example/original
& <PYTHON> <SKILL>/scripts/memory.py --project game check
& <PYTHON> <SKILL>/scripts/memory.py --project game memory
```

发现补丁是一个使用上述描述字段的 JSON 对象。嵌套字典会合并；列表和标量替换原值。空列表可清除已解决的问题。核心路径、源文件快照和检查点有专用命令，不能通过发现补丁覆盖。`configure` 只更新所提供的路径并保留发现。同一项目名称下更换游戏根目录会被拒绝；应创建新项目，避免混合证据。

`observe` 只记录显式选定且位于游戏根目录内的路径。添加 `--hash` 可计算文件哈希，但应考虑大型归档的开销。`checkpoint` 在记录前验证所提供的产物确实存在；`--hash` 可计算产物文件的哈希。它会替换该阶段原有检查点，因此应包含所有需要继续关联到该阶段的产物。

依赖已保存进度前，运行 `check` 并检查相关发现。它验证已观察源文件和已完成阶段产物的存在性及记录的元数据或哈希。路径缺失或改变时，需要重新检查受影响阶段。检查通过只覆盖已记录路径，不等于完整扫描游戏目录、证明引擎识别正确或验证映射语义。仅检查元数据可能漏掉大小和时间戳未变的内容变化。目录快照不会递归验证内容。

为 GalTTS 生成映射 JSON 时，保留约定结构，并单独验证文件与文本对应关系。检查点和记忆不会翻译源文本或验证语音质量。用户要求停止的任务应保持停止，直到新的授权请求要求继续。
