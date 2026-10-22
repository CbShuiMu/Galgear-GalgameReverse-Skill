# KiriKiri / KiriKiri Z：XP3 与 KAG / TJS

本页覆盖通用 XP3 容器与所引 KiriKiri Z 文本流；KAG 是脚本层，XP3 中也可以存放其他脚本和媒体。

## 解包与封包工具

| 工具与来源 | 解包或读取用途 | 封包或重建用途 | 适用范围与限制 |
| --- | --- | --- | --- |
| [GARbro CLI](../commands/garbro.md)，随附；[XP3 实现][garbro-xp3] | 识别、列出并解包支持的 XP3；读取器也能定位部分附加在 EXE 后的 XP3 | 创建 XP3 v1 / v2，可配置索引压缩、成员压缩及保留目录 | 写入能力不代表支持所有加密插件。CLI 的复杂 `Scheme` 不能直接赋值；需特殊方案且无法表达时停止，不用普通 XP3 冒充兼容产物 |
| KiriKiri Z 引擎[文本流实现][text]，外部源码参考 | 核对 BOM、默认编码、简易变换和压缩文本流的读取顺序 | 描述对应文本流写入方式；不是本技能的独立脚本 CLI | 不提供 TJS 字节码反编译或任意游戏专用过滤器；不需要运行游戏来阅读源码 |

归档命令使用 `i` → `l` → `x`；需要封包时先查 `options XP3`，保留目录设置为 `RetainDirs=true`。完整参数见工具文档。

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
- `.ks` 不保证是 KAG 明文，`.tjs` 也可能是字节码。发现 PSB 或编译场景时，按文件头分流到 [Emote / PSB](emote.md) 等对应资源页；XP3 成功解包不能证明脚本可编辑。
- 封包后用新目录重新解包，检查完整路径集合、数量及哈希；再核对脚本编码、引用和分支。补丁命名、加载顺序、密钥与特定插件参数由当前项目证据确认，不写成引擎通则。

## 来源、版本与验证边界

实现参考固定为 KiriKiri Z `fd5c4baa6a2ef5978db1bd043634351f48667daf` 和 GARbro `b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0`。本页为源码阅读等级，不声明真实游戏或运行验证。遇到非标准索引、专用过滤器、文本流模式或编码设置不符时失效，改查目标版本实现；项目特殊参数留在本地。

[archive]: https://github.com/krkrz/krkrz/blob/fd5c4baa6a2ef5978db1bd043634351f48667daf/base/XP3Archive.cpp
[text]: https://github.com/krkrz/krkrz/blob/fd5c4baa6a2ef5978db1bd043634351f48667daf/base/TextStream.cpp
[garbro-xp3]: https://github.com/morkt/GARbro/blob/b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0/ArcFormats/KiriKiri/ArcXP3.cs
