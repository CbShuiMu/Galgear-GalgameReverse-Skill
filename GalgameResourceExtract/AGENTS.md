# GalgameResourceExtract 工作约定

本文件适用于此技能目录及其子目录。执行提取任务前阅读 [SKILL.md](SKILL.md)，具体流程和命令以该文件及其引用资料为准。

## 入口与资料

- 项目状态入口是 `scripts/memory.py`；使用前阅读 [项目记忆](guides/memory.md)。`memory.example.json` 仅为结构示例。
- 引擎识别参考 [引擎与格式](catalog/engines.md)；按目标格式读取 `commands/` 中对应的 CLI 文档，不必一次加载全部资料。引擎页放在 `engine/`，以格式索引中的引擎标识命名。
- 映射结构参考 [对白与语音映射示例](assets/dialogue-audio-map.example.json)。随附工具位于 `tools/`，路径相对于本技能根目录解析。
- 映射与字节证据由 `scripts/validate_mapping.py` 只读检查，契约见 [对白映射](contracts/dialogue-audio.md)。没有宿主专用 API 依赖。
- 引擎方法按 [经验闭环](guides/engine-learning.md) 先查询再验证，成功后记录并按条件收录。`scripts/engine_experience.py` 使用标准库；用户证据不写入随包资料。

## 提取与交接约束

- 将归档提取、内部解压或解码、脚本解析分开处理。根据文件头和引擎证据选择工具，保留原始输入。
- 对白与语音按脚本中的实际引用关联，保留引用位置和消歧证据；不根据文件排序猜测。`audio_files` 与 `audio_paths` 必须等长并按索引对应，未确认音频的对白不进入最终映射。
- 需要说话人时，检查配套脚本、人物表和 ID 引用；保留可验证的实际姓名关联，未知身份或旁白按 `SKILL.md` 处理。
- 用于重建的基线目录保留原样字节及相对路径，解码音频、映射和工作记录另存。每个原始归档使用独立提取根目录，并将其交接为 GalTTS 的 `asset_root`。
- 用户路径、游戏历史和检查点保存在用户本地状态中；不要写入随包示例、技能文档或工具目录。复用状态前检查输入和产物是否变化。

## 维护与验证

- 工具运行文件、DLL、配置、`GameData/`、`_internal/` 和许可证应保持完整；普通文档或辅助脚本修改不需要重编译随附工具。
- 修改项目记忆逻辑后，在本技能根目录运行 `python scripts/test_memory.py`。该测试使用临时状态，不需要游戏资源。
- 修改映射校验后运行 `python scripts/test_mapping.py`。经验管理脚本在三个相关技能中保持一致，并从仓库根目录运行 `python -m unittest discover -s tests`。
- 修改提取或映射逻辑时，以代表性脚本验证引用、路径和数量，再检查受影响的批量输出。仅修改说明时核对链接和命令即可。
- 交付时报告绝对输出路径、已关联及未解决数量和验证限制；区分已确认事实与推测。
