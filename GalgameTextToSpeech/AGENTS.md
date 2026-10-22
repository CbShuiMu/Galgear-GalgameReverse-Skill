# GalgameTextToSpeech 工作约定

本文件适用于此技能目录及其子目录。运行任务前阅读 [SKILL.md](SKILL.md)，参数、状态和适配器协议以该文件及其引用资料为准。

## 入口与资料

- 主入口是 `scripts/galtts.py`；先阅读 [输入与命令](guides/inputs-and-commands.md) 和任务需要的 [后端适配器](guides/backends.md)。流程位于 `guides/`，映射契约位于 `contracts/`。
- `scripts/audio_formats.py` 负责源格式导出；`scripts/index_backend.py` 是可选 IndexTTS 适配器，`scripts/command_backend.py` 是通用命令客户端。
- `scripts/dialogue_mapping.py` 将对白记录规范化，`build_plan` 按实际资源分组；规则见 [映射到任务契约](contracts/dialogue-mapping.md)。共享资源不删除引用，多音频必须显式分段。
- 使用 `memory --where` 定位本地状态。`memory.example.json` 不是当前用户配置；模型环境、用户路径和运行历史应留在用户本地状态中。

## 生成与交接约束

- 复用用户选择的后端及其解释器，不预设 IndexTTS、硬件或模型路径。模型安装、下载和外部服务使用遵循已有授权；保留各模型的独立依赖环境。
- 使用当前确认的映射，先运行 `plan` 检查文本、路径、数量和格式支持。保留输入 JSON 及源音频。
- 新项目使用 `relative` 布局，保留相对于 `asset_root` 的路径。旧项目未指定布局时保持已有 `flat` 行为，迁移使用新输出目录。
- 保留支持的容器、编码、采样率和声道；不支持时报告具体文件和原因。仅当源文件、文本、模型及参数指纹和输出哈希匹配时复用已有结果。
- 按停止标记在当前条目完成后停止，保留进度。配置、状态、停止等控制命令应保持不加载模型。
- 完整批次生成后运行 `handoff` 或 `audit`；生成审计通过才交付完成状态的 `.galtts/resources.json`。`asset_root` 对应原始归档的原样资源根目录。
- 生成审计、解码长度及引擎边界验证、试听质量是不同检查，分别报告。用于游戏替换时按参考文档完成边界核验，不能以 `complete: true` 代替。

## 维护与验证

- 修改生成、续跑、音频导出或适配器行为后，在本技能根目录运行下面的检查。依赖见 `scripts/requirements.txt`；若 FFmpeg 不在 PATH 中，将 `$ffmpeg` 改为其绝对路径。

```powershell
$ffmpeg = (Get-Command ffmpeg -ErrorAction Stop).Source
python scripts/test_pipeline.py --ffmpeg $ffmpeg
```

- 测试使用临时合成音频和模拟后端，不启动真实模型或 GPU。交接协议变化时还应运行 GalPack 的 `scripts/test_resource_workflow.py`，命令见其 `AGENTS.md`。
- 映射规范化或任务分组变化时先运行 `python scripts/test_dialogue_mapping.py`，此检查不需要音频库或 FFmpeg。
- 仅改说明时核对链接和命令；不要为文档验证启动真实批次。交付实际输出路径、完成与失败数量、保留的非语言音频数量和未完成检查。
