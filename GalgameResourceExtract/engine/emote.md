# Emote / PSB：场景资源

PSB 是 Emote 使用的资源格式，也可用于其他场景资源；仅发现 PSB 文件不能证明整款游戏使用 Emote 引擎。本页按 Emote / PSB 格式族收录场景解析线索。

本页是格式参考，不随附通用 PSB 场景解析器。先检查提取后成员的文件头：同一个 XP3 可以包含普通 KAG 文本，也可以包含编译后的 `.ks.scn`，不能只按扩展名选解析器。

## 文件头与包装

未加密的 PSB v2+ 头部使用小端：magic 位于 0，u16 version 位于 4，u16 加密标记位于 6；names、字符串偏移表、字符串数据、chunk 偏移表、chunk 长度表、chunk 数据和根对象的 u32 偏移分别位于 12、16、20、24、28、32、36。v3 在 40 增加校验字段，v4 有额外 chunk 部分。每个偏移都须检查实际文件边界，不能把头长度当根对象位置。来源：[FreeMote PsbHeader](https://github.com/UlyssesWu/FreeMote/blob/master/FreeMote/PsbHeader.cs)。

原始 `PSB\0` 与 MDF 包装不同。普通 MDF 使用四字节 `mdf\0`、原始长度及偏移 8 开始的 zlib 流；加密壳需要已确认密钥。参见[PSB 包装说明](https://github.com/UlyssesWu/FreeMote/wiki/PSB-Shells%2C-Types%2C-Platforms)。

各段可能采用不同变换。分别验证头、names、对象和字符串；将解码视图另存为工作文件，记录原始与解码哈希、算法和坐标基准。随包证据校验器读取保存的实际文件，不假设宿主提供 XOR/zlib 视图服务。

## 紧凑数组与对象坐标

无符号数组的数量宽度为首 tag 减 `0x0c`。读取该宽度的数量后，再读取元素宽度 tag，用相同减法得到宽度，最后读取恰好 count 个元素。先限制数量、位宽和累计字节，再分配或遍历。

对象 tag `0x20` 是列表，其后为偏移数组，元素位置相对于该数组末尾。tag `0x21` 是字典，读取 key 和 value 两个数组后，value 位置相对于两数组末尾。`0x15..0x18` 是字符串池索引，宽度为 tag 减 `0x14`；经头部的字符串偏移表取偏移后，只加一次字符串数据基址。字符串为 NUL 结尾 UTF-8。来源：[GARbro PsbReader](https://github.com/morkt/GARbro/blob/master/ArcFormats/Emote/ArcPSB.cs)。

names 使用字符集、父节点和终端索引三个紧凑数组。按终端父链回溯，以 node 减 charset[parent] 恢复字节，逆序后按 UTF-8 解码；限制索引并检测环。names 是字典键，不是对白池。来源：[FreeMote LoadNames](https://github.com/UlyssesWu/FreeMote/blob/master/FreeMote.Psb/Psb.cs)。

## 还原实际场景引用

先检查根对象结构，再有界遍历场景记录，不扫描整个字符串池充当转录。上游场景识别器关注带 `scenes/name` 或无 chunks 的 `list/map` 根，但这只是候选线索。来源：[FreeMote ScnType](https://github.com/UlyssesWu/FreeMote/blob/master/FreeMote.Psb/Types/ScnType.cs)。

同时读取实际消息、显示姓名、语音字段及原生节点坐标。共享字符串的同一文本跨度可能被多个场景节点引用，必须分别保留出现记录；不能为了简化校验合并节点，也不能用字符串池物理顺序代替玩家阅读历史。

本地解析器保留完整字符串表索引、对象引用位置、索引操作数位宽、解析后的文本跨度及场景位置。文本与对象引用分别用[证据契约](../contracts/dialogue-audio.md)中的 message/reference 跨度记录；语音和姓名有各自的来源跨度。自动字节校验不证明某个对象引用就是剧情消息或有效存档坐标。

先核验一个代表性成员的文本、姓名、语音和坐标，再批量处理。结构错误时修复具体字段、基址或边界假设；无需重复解包未发生变化的容器。
