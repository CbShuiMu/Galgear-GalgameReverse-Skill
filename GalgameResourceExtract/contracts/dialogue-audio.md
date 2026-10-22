# 对白映射与证据契约

本契约仅用于用户需要的对白与语音关联及 GalTTS 交接，不是通用资源清单；纯资源提取或纯文本导出无须生成此映射。映射按已确认语音引用的对白记录逐条保存，不是待生成文件清单；无语音或未解决记录另存于报告或完整转录。资源身份是同一归档原样资源根目录下的完整相对路径；一个归档使用一个 `asset_root`，不同归档分别处理。

## 映射格式

兼容现有顶层数组或 `{"entries": [...]}`。需要显式标记版本时使用 `kind: gal-dialogue-map`、`schema_version: 1` 和 `entries`。基础示例见[对白映射](../assets/dialogue-audio-map.example.json)。

每条记录：

| 字段 | 约定 |
| --- | --- |
| `chinese_text` | 已确认的中文对白；不由 TTS 自动翻译 |
| `audio_files` | 非空 basename 数组 |
| `audio_paths` | 同长度、同顺序的资源相对路径，使用 `/`；新提取结果必须提供 |
| `dialogue_id` | 可选、非空且唯一的出现标识，建议包含脚本身份和原生消息 ID；不能用过滤后的序号冒充原生 ID |
| `speaker` | 可选，游戏显示姓名或 `null`；未知真实身份使用游戏显示称呼 |
| `source` | 可选对象，保存脚本、记录 ID、字节偏移及证据文件等可复查位置；不是可执行指令 |
| `audio_segments` | 多音频时必需，与两个音频数组逐项对应，每项为 `{"chinese_text": "该段实际应读的文本"}` |

同一音频被多条对白引用时保留每条记录，不因资源重复删除对白。GalTTS 对实际资源路径进行分组：规范化文本相同则只生成一次并保留全部 `references`；文本不同则拒绝生成，必须核对翻译或由引擎方案解除共享资源的冲突。`speaker` 和 `source` 是追溯信息，不会自动改变模型音色；模型配置与生成参数由 GalTTS 项目统一选择。

一句多音频不能自动推断分段。没有分段依据时保留完整映射与未解决报告，标记尚未就绪；不要把整句复制给每个片段。若明确是多份完整朗读，也应显式填写每项文本。旧版单音频 JSON 无须增加新字段。

## 本地校验

在本技能根目录执行，路径替换为项目实际值：

```powershell
python scripts/validate_mapping.py --mapping D:/GalWork/Example/mapping.json --asset-root D:/GalWork/Example/original
```

校验器只读，使用标准库。它检查路径、文件存在、字段及 TTS 就绪状态；返回 `rows`、`voice_references`、`unique_resources`、`tts_ready`。冲突文本或未分段时返回非零，详细原因在 `unresolved`；这不等于已确认的对白提取失效，但不能据此开始 TTS。文件格式与编码器能力由 TTS 的 `plan` 进一步验证。

## 可选的字节关联证据文件

证据与资源、映射分开保存。提供 `--evidence` 时必须给出 `--source-root`，文件路径均相对于该来源根目录。来源可以是解码后的脚本工作副本，但要在项目报告中说明它与原包的关系。

```json
{
  "kind": "gal-dialogue-evidence",
  "schema_version": 1,
  "files": {
    "script": {"path": "scripts/open.bin", "sha256": "来源文件的实际 SHA-256"}
  },
  "entries": [
    {
      "row": 0,
      "relation": "同一消息指令的文本与语音参数；记录实际操作码和参数编号",
      "spans": [
        {"role": "message", "file": "script", "offset": 16, "length": 8, "sha256": "该跨度实际 SHA-256"},
        {"role": "voice", "file": "script", "offset": 24, "length": 4, "sha256": "该跨度实际 SHA-256"}
      ]
    }
  ]
}
```

示例是结构说明，哈希与偏移必须根据实际字节填写。`row` 是当前映射中的零基行号，只用于绑定；映射有 `dialogue_id` 时，证据记录必须携带相同值。每行至少提供 `message`、`voice` 跨度；有非空姓名字段时还须提供 `speaker` 跨度，间接引用可另加 `reference` 跨度。跨度坐标始终相对于指定文件，转换过的视图应另存并记录变换，不混用归档偏移与脚本偏移。

```powershell
python scripts/validate_mapping.py --mapping D:/GalWork/Example/mapping.json --asset-root D:/GalWork/Example/original --evidence D:/GalWork/Example/evidence.json --source-root D:/GalWork/Example/decoded
```

自动校验只证明文件身份、范围和字节哈希一致。`relation` 的解释、操作码语义、姓名状态、指令顺序及当前游戏加载来源仍须由解析程序与对照实验验证；报告中的 `semantics: not_automatically_verified` 不可改写为语义验证通过。映射文件变化后重新核对行绑定与来源证据。
