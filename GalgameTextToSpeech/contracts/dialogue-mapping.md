# 从对白记录到生成任务

`scripts/dialogue_mapping.py` 只使用标准库，负责解释输入映射；`galtts.py build_plan` 再检查真实音频、解析资源身份并建立唯一生成任务。独立安装 GalTTS 不需要其他技能的脚本或宿主接口。

## 兼容输入

保留现有顶层数组和 `{"entries": [...]}`。显式版本格式是 `{"kind":"gal-dialogue-map","schema_version":1,"entries":[...]}`；未知 kind 或版本拒绝处理。每条记录的 `chinese_text`、`audio_files` 与可选 `audio_paths` 保持原语义。新提取结果应提供完整相对 `audio_paths`；旧版省略路径时仍只在 `asset_root/Voice/filename` 和 `asset_root/filename` 查找唯一文件。

可选的 `dialogue_id` 是唯一对白记录标识；`speaker` 为字符串或 `null`；`source` 为来源对象。它们保存在计划及交接清单的 `references` 中，不自动成为模型音色或生成参数。没有 `dialogue_id` 的旧数据仍通过 `row` 和 `voice_index` 追溯当前输入快照。

## 多段音频

同一句有多个文件时必须逐项提供 `audio_segments`，与 `audio_files`、`audio_paths` 等长同序。整体 `chinese_text` 继续保存完整对白，实际合成使用各段文本：

```json
[
  {
    "dialogue_id": "opening:12",
    "speaker": "角色甲",
    "chinese_text": "你好。我们出发吧。",
    "audio_files": ["001.wav", "002.wav"],
    "audio_paths": ["voice/001.wav", "voice/002.wav"],
    "audio_segments": [
      {"chinese_text": "你好。"},
      {"chinese_text": "我们出发吧。"}
    ]
  }
]
```

没有分段时预检查失败，不猜测文字边界，也不重复整句。显式分段为空或纯标点时沿用项目的非语言音频策略。段文本合并后不强制与完整对白字面相等，停顿、显示控制和朗读写法由用户或解析阶段确认。

## 共享资源与冲突

- 同一实际资源、相同规范化文本、同一项目配置：一个生成任务，保留全部对白引用。
- 同一实际资源对应不同文本：预检查失败，列出资源及冲突行；不能生成多份后覆盖同一路径。
- 不同目录的同名资源：`relative` 布局分别生成；`flat` 布局仍报输出冲突，不把它们当共享资源合并。

`total` 表示唯一资源任务数；`total_references` 表示语音引用数；`reused_references` 表示共享任务减少的重复次数。样本限制、停止、进度、审计数量都以唯一任务计数。原始映射不被修改，生成清单的每个资源只出现一次，引用列表包含零基 `row`、`voice_index` 及可选对白记录标识、姓名和来源。

文本仍按原规则清理换行转义及连续空白；仅增加引用不会改变相同资源文本的生成指纹，但映射哈希与交接清单会重新审计。文本、资源字节、模型或生成参数变化时继续使用原有指纹失效规则。证据来源信息仅用于追溯，计划器不据此执行代码或证明脚本语义。
