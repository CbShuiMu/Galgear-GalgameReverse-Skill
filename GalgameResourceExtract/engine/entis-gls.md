# Entis GLS / Cotopha：NOA、CSX 与 Cotomi 存档

## 解包与封包工具

| 工具与来源 | 解包或读取用途 | 封包或回写用途 | 适用范围与限制 |
| --- | --- | --- | --- |
| [GARbro CLI](../commands/garbro.md)，随附工具 | 识别、列出并解包支持的 NOA 归档；压缩/加密分支见[读取实现][noa] | 当前 NOA 实现不支持创建 | 以文件头、文件 ID 和当前工具配置核对；加密成员可能需要当前项目的密钥，不保证所有变体 |
| [EntisGLS_Tools：CSXTool][readme]，外部工具 | 提取 CSX 1.x 内联字符串 | 将修改文本回写 CSX，不创建 NOA | 上游声明的 1.x 范围；提取模式有适用差异，先验证代表性脚本 |
| [EntisGLS_Tools：CSXToolPlus][readme]，外部工具 | 提取 CSX 2.x–3.x 字符串 | 将修改文本回写 CSX，不创建 NOA | 按实际布局选择模式；随包仅有[类型源码摘录](../provenance/entisgls-tools/README.md)与许可证，没有完整工具或预编译程序 |

工具路径相对于本技能根目录。只需原样资源时，完成归档解包及成员核对即可；脚本解析、文本回写和存档分析按用户目标执行，分别验证。

## 格式特征与编码方式

| 格式或层级 | 通用识别特征 | 编码方式与判定依据 |
| --- | --- | --- |
| NOA 归档 | 所引实现检查 `Entis\x1a` / `VIST\x1a`、文件 ID `0x02000400`，从 `0x40` 的 `DirEntry` 读目录 | 旧 `EMSAC-Binary Archive` 分支的文件名使用 CP932；其他分支按实际目录编码配置确认。成员另有原样、压缩或加密分支，不能套用目录字符编码；见[NOA 实现][noa] |
| CSX 脚本 | 64 字节头，描述含 `Cotopha Image file`；随后是 8 字节 tag、8 字节小端长度和段正文 | 本页所引实现的宽字符串为 UTF-16LE，长度是 UTF-16 代码单元数，非字节数；见[读取函数][wide]。1.x 通常内联于 `image`，2.x–3.x 通常使用 `conststr`，也须检查内联分支 |
| Cotomi 存档 | `cotomi context file` 可作为候选标记，仍须确定它在实际文件中的层级 | 未确认统一的存档布局与字符编码；从容器边界及同版本读取实现核验，不能直接套用 CSX 编码或猜测压缩算法 |
| 图像、音频及其他成员 | 重新检查解包后成员的文件头和资源类型，不由 `.noa` 推断内部格式 | 媒体编码按各成员格式确定；归档解包、媒体解码和脚本文本解码分开处理 |

适用版本与验证等级：CSX 依据 Crsky 的 [EntisGLS_Tools 固定版本][tools]（`ccc67f537f56302fedae91b12ad8eff5ce8b4d62`），NOA 依据下方固定版本实现；本页为实现参考，未声明真实样本或游戏运行验证。文件头、版本、段布局或读取分支不符时停止套用，重新确认格式。单款游戏的特殊编码、偏移、密钥与资源覆盖规则保存在本地记录。

## 注意事项

### 分层解析与坐标

需要解析 CSX 内容时，本地解析程序保存完整字符串表、原始索引及 `image` 中的实际操作数引用；需要对白与语音关联时再保留对白记录。转换坐标时只加一次基址，不能用文本直接命中代替指令引用验证。来源和字节跨度按[映射与证据契约](../contracts/dialogue-audio.md)保存。下方伪代码仅示意流程，必须补齐输入长度检查。

1. **NOA 归档层**：先用 [GARbro CLI](../commands/garbro.md) 列表，记录归档名、内部完整路径、压缩/加密状态。提取后重新检查内部文件头，不把归档偏移当作 CSX 偏移。
2. **CSX 文件层**：验证头，再遍历段表，保存每段的头偏移、正文偏移和正文长度。
3. **段内结构**：仅在相应段正文内读计数和记录；读取全表后再筛对白。
4. **指令与语义**：需要语义解析时核对 `image` 中的引用和调用，按目标确认相应字段；对白与语音关联任务再确认对白、姓名、语音及顺序。字符串表包含代码标识符、标签和界面文字，不等于剧情顺序。

[GARbro 的固定版本 NOA 实现][noa]识别 `Entis\x1a` / `VIST\x1a` 与文件 ID `0x02000400`，从 `0x40` 的 `DirEntry` 开始读索引；条目偏移以当前目录记录起点为基准。文件记录正文通常在条目偏移加 16 字节处，另有压缩/加密分支。优先调用现有工具，避免只截取索引的逻辑长度而漏掉封装或解压步骤。

NOA 与 CSX 可共享 Entis 外层标记，不能只凭 `Entis` 判为同一种内容。GARbro 的 `IDR_COTOMI` XML 检查可定位归档密钥；这段实现**没有证明**游戏的资源加载先后关系。

### CSX 段头与坐标

[文件头类型][fileheader]与[加载函数][loader]给出 64 字节头：`magic[8]`、`u32 file_id`、`u32 reserved`、`description[48]`。小端 magic 为 `45 6e 74 69 73 1a 00 00`，描述前 18 字节为 `Cotopha Image file`。不要强行把 NOA 的文件 ID 要求套给 CSX。

随后每段为 **8 字节 tag + 8 字节小端 length + length 字节正文**。上游以有符号 64 位读 length；解析时拒绝负数、溢出与越界。对非负长度可用 `u64le`，但仍须上界校验。tag 含空格，如 `header  `、`image   `、`conststr`，不可按变长字符串移动游标。段正文起点是段头加 **16**，不是加 8。未知段按长度跳过，零 tag 和尾部剩余字节应记录原因，不能悄悄假定全文件已解析。

```text
pos = 64
while pos + 16 <= file_size:
    tag = bytes[pos : pos+8]
    length = u64le(pos+8)
    body = pos + 16
    require length <= file_size - body
    sections.append({tag, header: pos, body, length})
    pos = body + length
```

分析记录中显式保存下列坐标：`archive_offset`、`csx_file_offset`、`section_header_offset`、`section_body_offset`、`image_offset`、`string_index`。`image` 正文起点记为 `image_base`；已验证为 image 相对地址的值 `r`，才可换算 `csx_file_offset = image_base + r`。再次从归档读原始字节时，还须使用已验证的条目封装/解压规则，不能机械相加。

### conststr：必须保留空条目和原始索引

`conststr` 正文为 `i32 count`，随后每个原始编号依次为 `i32 UTF16单位数 → UTF16文本 → i32 引用数 → u32[引用数]`。空字符串也有引用数字段和引用数组，仍占一个编号；没有独立的 `nline` 或偏移表。先完整走表到精确段尾，再处理目标文本，不能用最大命中率拟合偏移。

由[段类型][constsection]、[条目类型][constentry]、[DWORD 数组][dwordarray]及[宽字符串读取][wide]可直接核对字段顺序。计数位于 **`conststr` 正文**，不是 tag 或 length 位置。全部数值小端；计数和字符串长度为 `i32`，引用元素为 `u32`。

```text
require conststr_length >= 4
p = conststr_body; count = i32le(p); p += 4
require count >= 0 and count <= (section_end - p) / 8
for string_index in range(count):
    require p + 4 <= section_end
    units = i32le(p); p += 4
    require units >= 0 and units <= (section_end - p) / 2
    raw = bytes[p : p + 2*units]; p += 2*units
    text = utf16le(raw)             # units 是 UTF-16 代码单元，不是字节数
    require p + 4 <= section_end
    ref_count = i32le(p); p += 4    # 空字符串之后仍有这个字段
    require ref_count >= 0 and ref_count <= (section_end - p) / 4
    refs = [u32le(p + 4*j) for j in range(ref_count)]
    p += 4*ref_count
    entries.append({string_index, text, refs})  # 不丢空条目、不重新编号
require p == section_end           # 不等则调查版本、基址或字段假设
```

保留 `raw` 或其哈希和完整记录边界用于核验。不要先删空字符串、去重、排除控制串或按中文正则过滤再建立索引：这样会令后面的所有引用整体错位。展示层可以筛选，原始表与 `string_index` 必须完整。

### 交叉验证 image 引用

[反汇编器][disasm]从独立的 `image` 正文字节流读取代码；其字符串操作数是 `u32 length_or_marker`：若为 `0x80000000`，随后为 `i32 string_index`；否则退回 4 字节按内联宽字符串读取。普通即时字符串加载的示例为 `02 00 06`（Load / Immediate / String），随后为字符串操作数。其他指令也能引用字符串，不能把该字节模式当成全量反汇编器。

`conststr.refs` 的原始类型只说明它是 `u32[]`，不能仅靠类型名证明每个值的坐标与指令位置。在支持的样本上可检验以下候选：`image[r:r+4]` 是当前索引，`image[r-4:r]` 是标记；此时 `r` 指向**索引字段**，并非指令起点或标记。先抽样，再统计全表的一致率、越界和例外；不通过时调查，不能为凑匹配率默默换基址或固定加减偏移。

最小程序应先输出段表、原始字符串数、空条目数、段末游标、引用匹配统计和少量经过边界核验的样例。形成可检验布局后立即保存并测试程序，再做全量语义提取。不要为读出更多字符串而继续无目标扫描。对白与姓名/语音关联须来自调用结构、参数和实际文件；未知姓名保留未知。

### 版本、语言和资源覆盖

若多个归档/散文件含同名脚本，分别记录候选来源、哈希、文件头、段表和语言。**本页引用的源码不足以确立通用 first / last 加载规则。** XML 的声明顺序、文件名、修改时间、解包器枚举顺序和文本可读性，单独都不能证明运行时赢家。

优先查同一安装的配置、可引用的加载代码或可重复运行证据，逐项写入该游戏工作目录的证据文件；链接观测与候选哈希。存档标题的字节精确匹配可帮助排除不一致版本，但同文重复命中不能单独证明优先级或执行路径。证据不足就明确未解决，不把其他安装/历史产物中的顺序升级为通用事实。

### Cotomi 存档：当前标题与运行状态分开验证

观察到 `cotomi context file` 时，先确认它所在的真实层级：它可能处于图像预览之后，也可能是独立对象文件。检查容器边界、长度、编码和可能的压缩层，不以扩展名或任意 UTF-16 扫描代替结构解析。

可读的存档标题/预览对白能与候选脚本做精确核验，并为当前定位提供锚点。它不自动给出执行指针、已读历史、路线、时间顺序或姓名。重复文本要结合可验证上下文消歧；标题截断/控制码清理要保留原始字节和规范化规则。压缩运行状态必须按有证据的算法解码，失败时报告缺少的格式证据；不得猜偏移、猜解压参数、把附近整数当作 PC，或把脚本物理前缀当作玩家已读历史。

先完成当前指定存档，再用独立第二样本验证可泛化性。只支持标题定位时如实标注局限；不能靠缩小测试、伪造历史或降低独立验证门槛宣告成功。

[tools]: https://github.com/crskycode/EntisGLS_Tools/tree/ccc67f537f56302fedae91b12ad8eff5ce8b4d62
[readme]: https://github.com/crskycode/EntisGLS_Tools/blob/ccc67f537f56302fedae91b12ad8eff5ce8b4d62/README.md
[fileheader]: ../provenance/entisgls-tools/CSXToolPlus/Types/FileHeader.cs
[constsection]: ../provenance/entisgls-tools/CSXToolPlus/Sections/SectionConstString.cs
[constentry]: ../provenance/entisgls-tools/CSXToolPlus/Types/ConstStringEntry.cs
[dwordarray]: ../provenance/entisgls-tools/CSXToolPlus/Types/DwordArray.cs
[wide]: ../provenance/entisgls-tools/CSXToolPlus/Extensions/BinaryReaderExtensions.cs
[loader]: https://github.com/crskycode/EntisGLS_Tools/blob/ccc67f537f56302fedae91b12ad8eff5ce8b4d62/CSXToolPlus/ECSExecutionImage.cs
[disasm]: https://github.com/crskycode/EntisGLS_Tools/blob/ccc67f537f56302fedae91b12ad8eff5ce8b4d62/CSXToolPlus/ECSExecutionImageDisassembler.cs
[noa]: https://github.com/Alex123666tw/GARbro-cli/blob/7b9160f4ea51cca6987ec96f895941de1780e1b6/ArcFormats/Entis/ArcNOA.cs
