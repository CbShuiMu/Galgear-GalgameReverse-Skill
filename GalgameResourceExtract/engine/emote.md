# Emote / PSB：场景资源

PSB 是 Emote 使用的资源格式，也可用于其他场景资源；仅发现 PSB 文件不能证明整款游戏使用 Emote 引擎。

## 解包与封包工具

| 工具与来源 | 解包或读取用途 | 封包或重建用途 | 适用范围与限制 |
| --- | --- | --- | --- |
| [GARbro CLI](../commands/garbro.md)，随附工具 | 实际外层为支持的 XP3 等归档时，列出并提取 PSB 成员 | 可创建的外层格式以 `f --writable` 为准；XP3 参数见命令文档 | 归档能力不等于 PSB 场景解析或重建；加密方案须另行核对，不能因发现 PSB 就假定外层是 XP3 |
| [FreeMote：PsbDecompile](../commands/freemote.md)，随附 v4.9.0 CLI | 将支持的 PSB / SCN 及普通 MDF 解析为 JSON 和原样资源块 | 不负责重建；配合 PsBuild 使用 | 按文件头、PSB 版本、类型和壳确认支持；扩展名相同不代表格式相同。随附裁剪没有外部媒体转换和压缩壳插件 |
| [FreeMote：PsBuild](../commands/freemote.md)，随附 v4.9.0 CLI | 使用 PsbDecompile 的工作产物 | 从 JSON 和资源重建支持的 PSB / SCN、普通 MDF | 保留配套资源及 `.resx.json` 中的版本、平台、编码和壳上下文；不替代外层归档封包，也不保证所有游戏变体兼容 |

## 格式特征与编码方式

| 格式或层级 | 通用识别特征 | 编码方式与判定依据 |
| --- | --- | --- |
| PSB v2+ | 原始标记为 `PSB\0`；小端头部包含版本、加密标记及各表偏移，v3/v4 增加字段 | 所引实现默认按 UTF-8 读取 NUL 结尾字符串，names 键也按 UTF-8 还原；见[字符串读取][psb-reader]与[names 实现][psb-names]。自定义编码选项不能作为引擎默认值，遇到不符时核查版本和读取实现 |
| 普通 MDF 壳 | `mdf\0` + 4 字节原始长度，从偏移 8 开始为压缩流 | 使用 zlib；这是压缩包装，不是字符编码。先还原 PSB，再按其内部结构读取字符串；见[MDF 实现][mdf] |
| 加密 PSB 或加密壳 | 根据头部标记、壳识别和同版本实现确认变换层级 | 密钥与变换参数由当前项目证据确定；不能把某款游戏的解密参数推广为 PSB 通则 |
| 外层归档与 chunk 资源 | 外层和成员分别检查文件头；chunk 可承载不同媒体资源 | 归档、PSB 字符串及媒体数据分别判定格式和编码，不能用 UTF-8 去解释整个文件或媒体 chunk |

适用版本与验证等级：格式依据下文 GARbro 与 FreeMote 固定源码。随附 CLI 已在隔离目录验证合成 SCN 的 PSB v2/v3/v4 字符串、原样资源块及普通 MDF 往返；未声明真实样本、所有 PSB 类型或游戏运行验证。版本、壳、表布局、类型处理或字符读取规则不符时停止套用，改查对应实现；项目特殊编码与密钥留在本地。FreeMote 的 CC BY-NC-SA 4.0 与依赖许可见命令页和工具目录。

## 注意事项

### 文件头与包装

随附 FreeMote 提供结构读写，不自动证明场景语义或对白与语音关联。先检查提取后成员的文件头：同一个 XP3 可以包含普通 KAG 文本，也可以包含编译后的 `.ks.scn`，不能只按扩展名选解析器。

未加密的 PSB v2+ 头部使用小端：magic 位于 0，u16 version 位于 4，u16 加密标记位于 6；names、字符串偏移表、字符串数据、chunk 偏移表、chunk 长度表、chunk 数据和根对象的 u32 偏移分别位于 12、16、20、24、28、32、36。v3 在 40 增加校验字段，v4 有额外 chunk 部分。每个偏移都须检查实际文件边界，不能把头长度当根对象位置。来源：[FreeMote PsbHeader](https://github.com/UlyssesWu/FreeMote/blob/master/FreeMote/PsbHeader.cs)。

原始 `PSB\0` 与 MDF 包装不同。普通 MDF 使用四字节 `mdf\0`、原始长度及偏移 8 开始的 zlib 流；加密壳需要已确认密钥。参见[PSB 包装说明](https://github.com/UlyssesWu/FreeMote/wiki/PSB-Shells%2C-Types%2C-Platforms)。

各段可能采用不同变换。分别验证头、names、对象和字符串；将解码视图另存为工作文件，记录原始与解码哈希、算法和坐标基准。随包证据校验器读取保存的实际文件，不假设宿主提供 XOR/zlib 视图服务。

### 紧凑数组与对象坐标

无符号数组的数量宽度为首 tag 减 `0x0c`。读取该宽度的数量后，再读取元素宽度 tag，用相同减法得到宽度，最后读取恰好 count 个元素。先限制数量、位宽和累计字节，再分配或遍历。

对象 tag `0x20` 是列表，其后为偏移数组，元素位置相对于该数组末尾。tag `0x21` 是字典，读取 key 和 value 两个数组后，value 位置相对于两数组末尾。`0x15..0x18` 是字符串池索引，宽度为 tag 减 `0x14`；经头部的字符串偏移表取偏移后，只加一次字符串数据基址。所引实现的字符串为 NUL 结尾 UTF-8。来源：[GARbro PsbReader][psb-reader]。

names 使用字符集、父节点和终端索引三个紧凑数组。按终端父链回溯，以 node 减 charset[parent] 恢复字节，逆序后按 UTF-8 解码；限制索引并检测环。names 是字典键，不是对白池。来源：[FreeMote LoadNames][psb-names]。

### 还原实际场景引用

本节用于用户需要场景语义或对白与语音关联的任务。只需原样 PSB 成员时，完成容器解包及成员核对即可；需要图像、动画或其他节点时，按实际目标结构解析，不强制收集对白或语音字段。

先检查根对象结构，再有界遍历场景记录，不扫描整个字符串池充当转录。上游场景识别器关注带 `scenes/name` 或无 chunks 的 `list/map` 根，但这只是候选线索。来源：[FreeMote ScnType](https://github.com/UlyssesWu/FreeMote/blob/master/FreeMote.Psb/Types/ScnType.cs)。

需要对白与语音关联时，同时读取实际消息、显示姓名、语音字段及原生节点坐标。共享字符串的同一文本跨度可能被多个场景节点引用，必须分别保留出现记录；不能为了简化校验合并节点，也不能用字符串池物理顺序代替玩家阅读历史。

本地解析器保留完整字符串表索引、对象引用位置、索引操作数位宽、解析后的文本跨度及场景位置。文本与对象引用分别用[证据契约](../contracts/dialogue-audio.md)中的 message/reference 跨度记录；语音和姓名有各自的来源跨度。自动字节校验不证明某个对象引用就是剧情消息或有效存档坐标。

先核验一个代表性成员的目标字段和坐标，再批量处理；做对白与语音关联时包含文本、姓名及语音。结构错误时修复具体字段、基址或边界假设；无需重复解包未发生变化的容器。

[freemote]: https://github.com/UlyssesWu/FreeMote/blob/d87be1f3b8458c81822825fd6d56123d4df860b4/README.md
[psb-reader]: https://github.com/morkt/GARbro/blob/b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0/ArcFormats/Emote/ArcPSB.cs
[psb-names]: https://github.com/UlyssesWu/FreeMote/blob/d87be1f3b8458c81822825fd6d56123d4df860b4/FreeMote.Psb/Psb.cs
[mdf]: https://github.com/UlyssesWu/FreeMote/blob/d87be1f3b8458c81822825fd6d56123d4df860b4/FreeMote/MPack.cs
