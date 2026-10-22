# 输入、导出与命令

## JSON 约定

使用现有 GalGame 对白映射结构。支持顶层数组和 `{"entries": [...]}`。共享语音、分段与对白记录标识的完整规则见[映射到任务契约](../contracts/dialogue-mapping.md)。示例对白保留中文，因为它是合成输入：

```json
[
  {
    "chinese_text": "你好，欢迎来到这里。",
    "audio_files": ["line_0001.ogg"],
    "audio_paths": ["Voice/line_0001.ogg"]
  }
]
```

- `chinese_text` 必须包含已确认的中文对白，允许中英混合。日文原文尚未翻译或缺少中文字段时，应补齐翻译。不要静默替换为原文。脚本不会翻译。
- `audio_files` 与 `audio_paths` 按索引对应。多个音频必须显式提供同序 `audio_segments`，各段使用各自的 `chinese_text`。输入路径相对于 `asset_root`，且必须位于其中。
- 未提供 `audio_paths` 时，只搜索 `asset_root/Voice/filename` 和 `asset_root/filename`。匹配存在歧义会报错。
- 新项目默认 `--output-layout relative`：按相对于 `asset_root` 的路径写入输出目录，保留目录、文件名及大小写。`Voice/char_a/001.wav` 与 `Voice/char_b/001.wav` 是不同输出。同一资源的相同文本引用合并成一个任务并保留全部引用，不同文本引用会报冲突。
- 已保存但没有布局设置的旧项目继续使用旧版 `flat` 输出。显式 `--output-layout flat` 只按基本文件名输出，并拒绝同名文件。迁移旧项目时，配置 `--output-layout relative` 和新的输出目录；不会移动或覆盖旧结果。两种布局都会在交接清单中导出原始资源路径。
- 对空文本或纯标点文本，根据项目设置复制原音频或报错。`copy` 保留非语言声音；不要声称这些条目已合成为中文。
- 预检查列出 JSON 映射的任务，不会静默将未映射资源加入批次。

## 保留源格式的含义

检查实际音频流，识别容器、编码、采样率和声道数，并保留能够确定的 PCM/FLAC 位深。显式导出规则覆盖 WAV、FLAC、MP3、OGG/Vorbis、OGG/Opus、M4A/AAC、M4A/ALAC 和 AIFF 等常见组合。以预检查结果为准。如果缺少编码器、容器不受支持、文件损坏或扩展名与容器不符，不要仅修改扩展名后继续。

模型先输出 PCM WAV，再进行一次目标格式编码。无损中间 WAV 不会增加一次有损压缩。Vorbis 默认 q=5，可通过项目的 `vorbis_quality` 配置。有损格式重新编码无法保证相同码率、文件大小、元数据或编码器配置。上采样或增加声道数无法创造缺失的音频细节；多声道输出通常由单声道 TTS 上混，不能重建原始空间声场。

## 游戏解码与越界验证

替换语音需要重新封装或装入游戏时，在封包前验证以下项目，并对最终归档原样提取后的资源重复检查。普通播放器或 FFmpeg 能播放、归档往返哈希一致，都不能证明目标引擎解码时不会越界。

- **确定目标规则。** 从原始资源和目标游戏的引擎版本、实际解码器确定长度字段的含义、单位和缓冲区分配方式。区分压缩字节数、每声道采样帧数、交错 PCM 字节数及容器头尾开销；不要跨引擎套用某个格式的偏移或公式。
- **逐条检查资源。** 核对声明的压缩/解压长度、数据块与偏移边界、采样率、声道、位深、块对齐，以及格式提供的校验信息。检查字段可表示范围和整数溢出，拒绝截断、损坏或长度不一致的结果。不能复制旧语音长度，或用时长、码率估算替换后的长度。
- **核对真实解码输出。** FFmpeg 与游戏解码器可能对编码延迟、首尾裁剪、填充和块边界采用不同处理，得到不同的 PCM 数据量；这不表示压缩音频文件本身被改写。对影响缓冲区分配的字段，按目标引擎自身或与其匹配的解码器口径测量输出字节数、核对写入边界，再确定应写入的长度；不能直接照抄 FFmpeg 的 PCM 输出大小。格式元数据可用于预检查，但采样数等元数据到字节数的换算也须经过目标引擎验证。
- **验证内存边界。** 在隔离进程中采用保护页、哨兵或可用的内存检测工具，按引擎真实容量检查越界读写，尤其覆盖短音频、长音频、编码块边界和原样保留的非语言音频，并以原始语音作对照。设置超时；崩溃、异常退出、超时、哨兵被改写或缺少完整结果都判为失败。不要用统一增加固定字节数的方式掩盖未知差异，也不要跨可执行文件复用硬编码函数地址。
- **记录验证范围。** 在项目交付报告中记录资源 SHA-256、引擎/解码器版本或可执行文件 SHA-256、检查方法、覆盖数量、声明与实测长度、失败项和最终归档复核结果。资源或解码器改变后重新验证。无法运行目标解码器时，分别报告结构检查结果和“引擎解码边界未验证”；不得写成“越界检查通过”或“游戏内播放已验证”。已知越界未修正前停止安装。

这些是按游戏执行的验证要求，现有 `plan`、`audit`、`handoff` 不会自动执行引擎级内存检查。`.galtts/resources.json` 的 `complete: true` 表示当前生成批次审计完整，不表示游戏兼容性或内存安全已经验证；将引擎验证证据单独记入项目报告。

向封包阶段交接时，附上已测资源的哈希、解码器身份、测量口径、声明与实测长度，以及边界验证状态。若 Pack 又进行了转码或重新封装，应对实际封装资源重新测量和记录哈希，并更新受影响的暂存与验证清单；不能将 TTS 输出的旧验证结论直接用于变化后的字节。长度字段错误应按格式修正，不能通过随意裁剪音频或统一增加 256 字节来凑数。

## 配置与命令

全新安装时，可使用现有 Python 解释器执行只依赖标准库的配置命令。运行 `memory --where` 定位用户状态，运行 `memory` 查看。文件不存在时，程序报告空配置，不创建文件。与用户确定后端，准备设置 JSON，注册模型配置并配置项目。没有预选的模型或项目。

将下方 `<PYTHON>`、`<SKILL>`、`<FFMPEG>`、`<ADAPTER>` 和 `<SETTINGS_JSON>` 替换为用户实际值，不要直接执行占位符。`<ADAPTER>` 可为 `index`、`command` 或自定义 Python 适配器文件，见[后端适配器](backends.md)。预检查与生成使用选定模型环境的 Python。全局参数 `--memory` 和 `--project` 放在子命令之前。

```powershell
& <PYTHON> <SKILL>/scripts/galtts.py memory --where
& <PYTHON> <SKILL>/scripts/galtts.py memory
& <PYTHON> <SKILL>/scripts/galtts.py profile my-tts --python <PYTHON> --ffmpeg <FFMPEG> --adapter <ADAPTER> --settings-file <SETTINGS_JSON>
& <PYTHON> <SKILL>/scripts/galtts.py --project game configure --input-json D:/Game/mapping.json --asset-root D:/Game/assets --output-dir D:/Game/ChineseVoice --profile my-tts
& <PYTHON> <SKILL>/scripts/galtts.py --project game plan
& <PYTHON> <SKILL>/scripts/galtts.py --project game run --limit 5
& <PYTHON> <SKILL>/scripts/galtts.py --project game run
& <PYTHON> <SKILL>/scripts/galtts.py --project game stop
& <PYTHON> <SKILL>/scripts/galtts.py --project game status
& <PYTHON> <SKILL>/scripts/galtts.py --project game run --resume
& <PYTHON> <SKILL>/scripts/galtts.py --project game audit
& <PYTHON> <SKILL>/scripts/galtts.py --project game handoff
```

`profile` 注册或更新命名模型配置，不会为项目选择它，也不会加载模型。`configure` 只更新所提供的项目字段，并记住输出目录变化。模型配置设置、生成参数及适配器内容均参与指纹计算。源音频、对白或这些设置变化时，旧结果失效。已有同名输出若未经本工具验证，会阻止执行。应使用新输出目录，或在明确授权后迁移或替换它们；不要直接覆盖。

用户状态在 Windows 默认位于 `%LOCALAPPDATA%/GalTTS/memory.json`，其他系统为 `$XDG_STATE_HOME/gal-tts/memory.json`，未设置时回退到 `~/.local/state/gal-tts/memory.json`。`GAL_TTS_HOME` 设置替代状态目录；`--memory ABSOLUTE_PATH` 显式选择文件。相关命令保持相同状态选择。`memory.example.json` 有意保持为空。不要把用户正在使用的状态、机器路径、凭据或运行历史复制到共享技能包。

输出目录的 `.galtts/` 保存预检查结果、计划、源 JSON 快照、`manifest.jsonl`、`progress.json`、中间 WAV、日志、`audit.json` 和 `resources.json`。源 JSON 和资源保持不变。续跑只跳过指纹和文件哈希均匹配的成功结果。默认每个条目最多重试两次。停止标记在当前条目完成后生效。只有用户新近要求开始或恢复该批次时，才使用 `--resume`。

`handoff` 在不加载模型的情况下审计全部当前映射，并导出 `.galtts/resources.json`。只有生成审计通过才设置 `complete: true`；样本与审计失败的结果不能作为完整替换集使用。每个条目记录原始相对 `path`、原文件路径及哈希和大小、生成文件路径及哈希和大小、操作及指纹。顶层结构使用 `kind: gal-resource-manifest`、`schema_version: 1` 和 `stage: generated`，并记录映射 JSON 哈希及原始和输出根目录。更改配置后或封包前重新运行 `handoff`。直接交接给 GalPack 时，用一个归档的原样资源根目录作为 `asset_root`；不同归档根目录应分开处理。

`run --limit N` 产生 `sample_completed`，不得报告为全部完成。`audit` 始终检查整个映射。通过格式和哈希检查不能证明试听质量、发音、情感或音色相似度。为新模型、角色或设置生成样本并试听；有帮助时比较 ASR 转录。用户明确直接要求完整批次时，遵循该要求，不额外增加样本审批步骤。

Windows 上用 PowerShell `Start-Process -WindowStyle Hidden` 启动长任务，将 stdout 和 stderr 重定向到任务日志；其他系统使用适合该主机的后台任务机制。报告真实 PID、输出目录和进度。创建技能、注册配置、读取配置、`plan` 和 `status` 都不得启动模型。用户要求停止后保留结果。只有用户要求时才配置自动重启或提醒。

## 验证技能

`scripts/requirements.txt` 只列出批处理层依赖。检查所选模型环境是否已满足要求，只安装缺少的依赖，避免升级模型固定版本的依赖。`scripts/test_pipeline.py --ffmpeg ABSOLUTE_PATH` 在临时目录中使用合成测试音频，验证混合格式导出、配置记忆、续跑、停止、指纹、路径和命令适配器，不加载真实模型。通过此检查不能证明新接入的模型已成功合成音频。

