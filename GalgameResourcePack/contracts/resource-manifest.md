# 资源清单契约

本契约定义 `scripts/resource_workflow.py` 与 GalTTS 交接时使用的清单。执行顺序见[资源交接流程](../guides/resource-workflow.md)，辅助脚本参数见[资源辅助命令](../commands/resource-workflow.md)。

## 身份与阶段

所有交接清单使用 `kind: gal-resource-manifest`、`schema_version: 1`、`stage`、`complete` 标记及 `entries` 数组。

| 阶段 | 生成方 | 内容 |
| --- | --- | --- |
| `extracted` | `resource_workflow.py init` | 所有原始资源及其源路径、大小、SHA-256，原始归档身份信息，目标格式及显式创建选项 |
| `generated` | `galtts.py handoff` 或通过的完整 `audit` | 选定替换资源、原始与生成文件身份信息、映射身份信息、生成指纹与根目录 |
| `staged` | `resource_workflow.py merge` | 预期的完整或补丁资源集、保留或替换操作、预期哈希、暂存根目录与输入清单身份信息 |

生成阶段的 `resources.json` 保存在 TTS 输出的 `.galtts/` 目录下。只接受 `complete: true` 的清单。生成审计完整、暂存与归档字节一致、引擎边界验证和游戏运行各自独立；`complete` 不能证明后续验证通过。

## 根目录与资源路径

- 每个原始归档使用独立的原样资源根目录和基线清单。GalTTS 的 `asset_root` 指向该根目录。
- 条目的 `path` 使用 `/` 分隔符，标识原始归档内部资源，而非相对于游戏安装目录的路径。归档包含 `char_a/001.ogg` 时使用该路径，不人为添加 `Voice/` 前缀。
- 路径必须是相对路径，不得向上穿越父目录，并且忽略大小写后仍须唯一。
- 映射、清单、生成输出、暂存与验证目录都放在原样资源根目录之外；流程清单和报告也放在所有资源目录之外，避免混入归档。
- 相对路径布局与旧版扁平布局的 TTS 输出均携带原始条目路径；合并以此恢复目录，不按基本文件名推断。
