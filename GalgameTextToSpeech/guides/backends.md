# 后端适配器

将模型接入与批处理分开。默认不选择或下载任何模型。用户可以选择已有本地模型、已授权服务或其他后端。按用户的优先级评估中文支持、声音克隆需求、硬件、安装工作量和费用；不要假设用户使用 IndexTTS 或作者的硬件。

用户本地状态中的每个模型配置指定 Python 解释器、适配器、FFmpeg 可执行文件和设置。用 `galtts.py profile NAME --python PYTHON --ffmpeg FFMPEG --adapter ADAPTER --settings-file SETTINGS_JSON` 注册。`ADAPTER` 可为 `index`、`command` 或自定义 Python 适配器的绝对路径。内置适配器保存为 `builtin:index` 或 `builtin:command`，相对于本技能安装位置解析。设置必须是包含该后端实际配置的 JSON 对象。重新注册只更新所提供字段；直到项目通过 `--profile NAME` 配置前，不会为项目选择该配置。

使用该配置的 Python 启动批处理程序。切换模型不仅是更改模型名称：确认目标模型的真实入口与输入要求，必要时实现适配器，测试少量样本并保存验证后的配置。模型、Python 和 FFmpeg 的绝对路径应保存在用户状态中，不要写入分发的示例。

## Python 插件

适配器是提供以下接口的 Python 文件：

```python
def create_backend(settings):
    return Backend(settings)

class Backend:
    def synthesize(self, *, text, reference_audio, output_wav,
                   language, seed, options):
        # text 已是中文；reference_audio 是解码后的 PCM WAV。
        # 调用选定模型并写入 output_wav；失败时抛出异常。
        ...

    def close(self):
        # 可选：释放模型或关闭客户端。
        ...
```

遇到首个需要合成的任务时调用一次 `create_backend`，并在整个批次复用该实例。对声音克隆模型传入参考音频。不支持克隆的模型应使用用户选定的说话人，并说明无法保留原始音色。不要假设所有 TTS 模型支持相同的参数、情感、语言或采样率。

插件将模型输出统一为 PCM WAV。导出层随后匹配源音频实际的容器、编码、采样率和声道数。在各模型独立环境中管理依赖，不要为了添加其他模型而替换现有 IndexTTS 环境。

在同一路径替换或升级权重时，用官方修订版本或自定义权重的 SHA-256 更新配置中的 `model_revision`，使已有输出指纹失效。路径相同不能证明结果仍来自同一模型。

## 可选 IndexTTS 适配器

只有用户选择 IndexTTS 时才使用此适配器。将 `project_dir` 设置为其源码目录，并显式将 `version` 设置为 `"2"` 或 `"2.5"`；不会隐式选择版本。`model_dir` 可指向用户权重，否则使用所选版本的标准 `checkpoints_2` 或 `checkpoints` 目录。`half_precision` 默认 true，可配置（2.0 使用 FP16，2.5 使用 BF16）。保持模型常驻内存。生成选项、精度和 CPU 线程数应适合用户硬件与优先级。

可选 `cpu_encoder` 默认 false，启用时需要兼容的源码补丁；适配器会检查是否支持该参数。不要假设上游源码支持此补丁。不设置 `threads` 时保留 PyTorch 默认值，或检查用户 CPU 后再设置。本技能不指定 GPU 型号、显存大小或并发级别。

## 其他 CLI 或服务客户端

`scripts/command_backend.py` 与模型无关，支持读取请求 JSON 并写入 WAV 的客户端脚本。配置设置示例：

```json
{
  "argv": ["D:/OtherTTS/.venv/Scripts/python.exe", "D:/OtherTTS/client.py", "--request", "{request_json}"],
  "cwd": "D:/OtherTTS",
  "timeout_seconds": 600
}
```

此示例展示接入协议，不代表 OtherTTS 已安装或经过测试。独立的 `{request_json}`、`{output_wav}` 和 `{reference_audio}` 参数标记会替换为路径。命令不通过 Shell 执行，也不会把对白插入命令字符串。

请求 JSON 包含 `text`、`reference_audio`、`output_wav`、`language`、`seed` 和 `options`。客户端读取这些字段，调用对应 CLI 或本地 HTTP API，解码返回音频并写入 PCM WAV。持久服务可以复用已加载模型。HTTP 地址、请求结构及克隆参考音频的上传方式应以该服务实际文档为准。添加付费或外部服务时遵守用户授权范围。API 密钥应保存在环境变量或服务安全配置中，不要写入 `memory.json`。

目标模型提供 Python API 时，优先使用插件接口，避免每个音频文件都重新加载模型。
