# GalTTS 批处理命令

入口为 `scripts/galtts.py`。首次配置、生成与交接的执行顺序见[生成流程](../guides/generation.md)，输入规则见[映射到任务契约](../contracts/dialogue-mapping.md)。

## 解释器与参数位置

配置命令只依赖标准库；预检查与生成使用所选模型环境的 Python。将 `<PYTHON>`、`<SKILL>`、`<FFMPEG>`、`<ADAPTER>` 和 `<SETTINGS_JSON>` 替换为实际值，不直接执行占位符。全局参数 `--memory` 和 `--project` 放在子命令之前。

`<ADAPTER>` 可为 `index`、`command` 或自定义 Python 适配器文件，设置协议见[后端适配器](../guides/backends.md)。

## 状态与配置

```powershell
& <PYTHON> <SKILL>/scripts/galtts.py memory --where
& <PYTHON> <SKILL>/scripts/galtts.py memory
& <PYTHON> <SKILL>/scripts/galtts.py profile my-tts --python <PYTHON> --ffmpeg <FFMPEG> --adapter <ADAPTER> --settings-file <SETTINGS_JSON>
& <PYTHON> <SKILL>/scripts/galtts.py --project game configure --input-json D:/Game/mapping.json --asset-root D:/Game/assets --output-dir D:/Game/ChineseVoice --profile my-tts
```

`profile` 注册或更新命名模型配置，只更新所提供字段，不会为项目选择它；项目通过 `configure --profile NAME` 选择。`configure` 同样只更新所提供的项目字段，并记住输出目录变化。新项目默认 `relative` 布局，可通过 `configure --output-layout relative|flat` 显式选择；迁移规则见生成流程。

用户状态在 Windows 默认位于 `%LOCALAPPDATA%/GalTTS/memory.json`，其他系统为 `$XDG_STATE_HOME/gal-tts/memory.json`，未设置时回退到 `~/.local/state/gal-tts/memory.json`。`GAL_TTS_HOME` 设置替代状态目录；全局 `--memory ABSOLUTE_PATH` 显式选择文件。相关命令保持相同状态选择。文件不存在时读取返回空配置，不创建文件；`memory.example.json` 是空结构示例。用户状态、机器路径、凭据和运行历史不写入共享技能包。

## 计划、生成与控制

以下调用按当前任务选择，不作为依次执行的批次脚本：

| 调用 | 用途 |
| --- | --- |
| `--project game plan` | 预检查当前配置和整个映射 |
| `--project game run --limit 5` | 生成最多 5 个唯一资源任务的样本 |
| `--project game run` | 执行完整批次 |
| `--project game stop` | 请求在当前条目完成后停止 |
| `--project game status` | 查看状态与进度 |
| `--project game run --resume` | 按用户新的开始或恢复请求续跑 |
| `--project game audit` | 审计整个映射及已有输出 |
| `--project game handoff` | 审计并导出生成资源清单 |

调用时使用同一解释器和入口，例如：

```powershell
& <PYTHON> <SKILL>/scripts/galtts.py --project game plan
```

`memory`、`profile`、`configure`、`status`、`stop`、`plan`、`audit` 和 `handoff` 不加载模型。只有生成任务需要合成时才创建后端。指纹失效、已有输出冲突、停止与交接验收按生成流程处理；维护测试见本技能 [AGENTS.md](../AGENTS.md)。
