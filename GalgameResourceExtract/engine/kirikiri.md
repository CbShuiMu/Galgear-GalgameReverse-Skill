# KiriKiri / KiriKiri Z：XP3 与 KAG / TJS

本页覆盖通用 XP3 容器与所引 KiriKiri Z 文本流；KAG 是脚本层，XP3 中也可以存放其他脚本和媒体。

## 解包与封包工具

| 工具与来源 | 解包或读取用途 | 封包或重建用途 | 适用范围与限制 |
| --- | --- | --- | --- |
| [GARbro Mod CLI](../commands/garbro.md)，随附；[XP3 实现][garbro-xp3] | 识别、列出并解包支持的 XP3；读取器也能定位部分附加在 EXE 后的 XP3 | Mod CLI 不提供封包；需另选匹配的引擎工具 | 需匹配当前游戏的过滤器；解包成功不能证明封包或插件兼容性 |
| [序号解包 CLI](../commands/garbro-archive.md)，随附 | 含同名条目的 XP3 按索引序号提取，保留原名和偏移 | 无封包接口 | 逻辑流仍依赖匹配过滤器，归档签名与加载顺序须另验。 |
| KiriKiri Z 引擎[文本流实现][text]，外部源码参考 | 核对 BOM、默认编码、简易变换和压缩文本流的读取顺序 | 描述对应文本流写入方式；不是本技能的独立脚本 CLI | 不提供 TJS 字节码反编译或任意游戏专用过滤器；不需要运行游戏来阅读源码 |

使用 Mod 的 `GARbro.Console.exe ARCHIVE` 列表、`-x ARCHIVE` 解包；输出由工作目录指定。Mod CLI 不创建 XP3；完整参数见工具文档。自动识别失败时先确认索引结构和读取参数。标准未加密样本也可能因标题查找未命中、读取器发出的参数请求无人应答而报 `unknown format`。

## 格式特征与编码方式

| 层级 | 通用识别特征 | 编码或变换方式与判定依据 |
| --- | --- | --- |
| XP3 容器 | 标记为 `58 50 33 0D 0A 20 0A 1A 8B 67 01`；索引含 `File`、`info`、`segm` 等块 | 多字节整数按小端；标准 `info` 的名称为带长度的 UTF-16LE，不是 CP932；见[官方归档读取器][archive] |
| 索引与成员分段 | 索引压缩标志与成员 `segm` 压缩标志分别存在；成员可能分为多段 | 通用实现支持原样或 zlib 压缩。逐段合并并核对解压长度；解压与字符解码是两步，不能把整个 XP3 当文本 |
| KAG / TJS 明文 | 常见 `.ks`、`.tjs`，先检查实际内容和文件头 | 所引 Z 文本流识别 UTF-16LE BOM `FF FE`、UTF-8 BOM `EF BB BF`；无 BOM 时遵循引擎构建及 `-readencoding` 设置，Z 默认 UTF-8，兼容模式可用 Shift_JIS。不能把所有 KiriKiri 版本统一转成某一种编码 |
| 引擎文本流包装 | `FE FE` 后带模式字节，再带原始 UTF-16LE BOM | 模式 0 / 1 为简易字符变换，模式 2 为带长度字段的 zlib 压缩；这是文本流包装，不是 XP3 加密。按[实现][text]还原，再按 UTF-16LE 读取 |
| 归档过滤器与媒体 | XP3 读取器可调用外部 extraction filter；成员也可为 TLG、PNG、Ogg 等 | 过滤器不由 XP3 标记唯一决定。媒体按自身文件头和同版本解码器判断；文件名编码与音频编码无关 |

## 注意事项

- 原样资源根目录保留解包后成员字节及相对路径；文本包装解码、TLG 转图和脚本解析产物另存。记录工具是否额外执行成员过滤，避免把工作副本误作基线。
- 先核对 `info`、`segm`、`adlr`、完整名称与分段范围。整个索引符合标准分段且成员标志全为零时，可用 Mod 的读取 API 应答 XP3 参数请求，提供无额外归档过滤器的选项。此方式已在多个真实包对照历史索引和抽查成员，当前属于本地诊断路线。非零标志、非标准分段或未知过滤器须按已匹配方案处理，保留待验状态。
- Mod 的成员读取流可自动展开 MDF 等内部包装。已见同一脚本的旧标准段输出包含 MDF，Mod 返回内层数据。对照时先按 MDF 头的声明长度和压缩流边界独立解码，再比较同层级哈希；保留带包装的旧成员作封包基线。
- 若顶层索引含 `Hxv4`，常规列表可能只给出可见名称或占位记录。保留这一级证据，并用匹配版本的读取链逐包核验载荷；不能把常规列表或错误过滤器的输出视为成功。[Hxv4 索引实现参考][hxv4]
- `.ks` 不保证是 KAG 明文，`.tjs` 也可能是字节码。发现 PSB 或编译场景时，按文件头分流到 [Emote / PSB](emote.md) 等对应资源页；XP3 成功解包不能证明脚本可编辑。
- 封包后用新目录重新解包，检查完整路径集合、数量及哈希；再核对脚本编码、引用和分支。补丁命名、加载顺序、密钥与特定插件参数由当前项目证据确认，不写成引擎通则。

## 来源、版本与验证边界

实现参考固定为 KiriKiri Z `fd5c4baa6a2ef5978db1bd043634351f48667daf`、GARbro `b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0` 及 Mod 1.0.2.2 的 [XP3 参数请求][mod-xp3] 与 [成员流过滤][mod-filter]。Mod 迁移结论覆盖已核对的真实索引和抽样成员。非标准索引、专用过滤器、文本流模式和编码须按目标版本重新验证。封包及游戏内加载另验。

[archive]: https://github.com/krkrz/krkrz/blob/fd5c4baa6a2ef5978db1bd043634351f48667daf/base/XP3Archive.cpp
[text]: https://github.com/krkrz/krkrz/blob/fd5c4baa6a2ef5978db1bd043634351f48667daf/base/TextStream.cpp
[garbro-xp3]: https://github.com/morkt/GARbro/blob/b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0/ArcFormats/KiriKiri/ArcXP3.cs
[mod-xp3]: https://github.com/crskycode/GARbro/blob/102d19710c819ed363b7ea28f2d883ccaf922214/ArcFormats/KiriKiri/ArcXP3.cs
[mod-filter]: https://github.com/crskycode/GARbro/blob/102d19710c819ed363b7ea28f2d883ccaf922214/ArcFormats/KiriKiri/CryptAlgorithms.cs
[hxv4]: https://github.com/hktkqj/cxdec-hxv4-static-analysis/blob/3c6dee001df011fa7ed557c7463635c6f67698f6/docs/core/hxv4/01-hxv4-table.md

<!-- EXPERIENCE:9f5fd42f1afdcb8b6aabf396cfda3dd035140c24176d133c3945dec337864b1f:START -->
## 以序号保存同名 XP3 条目并核对索引身份

- 引擎版本：XP3 / 同名条目
- 方言/条件：Windows 真实样本，限已核对的读取范围
- 阶段：extract
- 验证等级：real_sample
- 经验 ID：`9f5fd42f1afdcb8b6aabf396cfda3dd035140c24176d133c3945dec337864b1f`

本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。

### 适用前提

- 用真实源文件和验证结果确认当前版本与读取层级。

### 已验证步骤

- 用固定版 GARbro Mod 的逻辑流读取。同名输出各用独立序号，核对偏移、长度、重复次数、哈希和可识别媒体头。

### 限制与失效条件

- 仅验证当前过滤器、索引成员和逻辑载荷；不确定加载优先级、封包与签名。

原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。
<!-- EXPERIENCE:9f5fd42f1afdcb8b6aabf396cfda3dd035140c24176d133c3945dec337864b1f:END -->

<!-- EXPERIENCE:0703e8bd6b7b74052c4eec6d30c721b5037f6e74350ff3fd9b38428b04fff19b:START -->
## 按 XP3 段索引复原未加密成员并逐条校验 Adler-32

- 引擎版本：XP3 / zero info flags / standard segments
- 方言/条件：Windows 真实样本，限所列的读取层及布局
- 阶段：extract
- 验证等级：real_sample
- 经验 ID：`0703e8bd6b7b74052c4eec6d30c721b5037f6e74350ff3fd9b38428b04fff19b`

本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。

### 适用前提

- 确认 XP3 签名、标准 File/info/segm/adlr 索引、零加密标志和匹配的段长度。

### 已验证步骤

- 区分容器解压和成员过滤。逐段核对输入及逻辑范围，将输出与索引逻辑长度、Adler-32 及代表媒体签名对照。

### 限制与失效条件

- 此路线只覆盖已证实无归档过滤的成员。加密、特殊段标志、文本包装和脚本语义需独立验证。

原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。
<!-- EXPERIENCE:0703e8bd6b7b74052c4eec6d30c721b5037f6e74350ff3fd9b38428b04fff19b:END -->
