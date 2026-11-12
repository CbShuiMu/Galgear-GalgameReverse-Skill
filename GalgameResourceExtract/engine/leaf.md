# Leaf：KCAP 与 LAC 归档

## 解包与封包工具

| 工具与来源 | 解包用途 | 封包用途 | 适用范围与限制 |
| --- | --- | --- | --- |
| [GARbro Mod CLI](../commands/garbro.md)，随附 | 识别 KCAP、LAC 两种归档并读取逻辑成员 | Mod CLI 只读。所引读取器无写入接口。 | PC 样本有多种布局。包扩展名也可能用于 ASF 视频。 |

## 格式特征与编码方式

| 层级 | 识别与验证 |
| --- | --- |
| KCAP | 文件头为 `KCAP`。用计数、索引起点、记录大小和首条载荷偏移的关系区分布局；所引实现对压缩成员使用 LZSS。零长度索引槽在所引读取器中被过滤。 |
| LAC | 文件头为 `LAC 00`。LAC 与 PAK/LAC 的名称字段、成员尺寸和布局须按相符的读取分支处理，不能沿用 KCAP 索引。 |
| 脚本和媒体 | 归档压缩与脚本、语音、图像的内部编码分别核对。`.pak` 也可能是以 ASF GUID 开头的独立视频。 |

## 注意事项

原版、追加和汉化包分别解包。核对索引槽、过滤条件及实际文件数。确认头为视频且工具输出覆盖整个文件时按散媒体归档，不计入 KCAP 或 LAC 容量。

来源为[固定版 KCAP 实现](https://github.com/crskycode/GARbro/blob/102d19710c819ed363b7ea28f2d883ccaf922214/ArcFormats/Leaf/ArcPAK.cs)与[LAC 实现](https://github.com/crskycode/GARbro/blob/102d19710c819ed363b7ea28f2d883ccaf922214/ArcFormats/Leaf/ArcLAC.cs)。

<!-- EXPERIENCE:536f2cee8f3e4e33f43b43af3e263da624e68fc4f5c3e407a5b2850f99936dc7:START -->
## 用 KCAP 索引记录大小和成员长度验证脚本包

- 引擎版本：KCAP 0x2c
- 方言/条件：Windows 真实样本，限匹配的归档布局
- 阶段：extract
- 验证等级：real_sample
- 经验 ID：`536f2cee8f3e4e33f43b43af3e263da624e68fc4f5c3e407a5b2850f99936dc7`

本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。

### 适用前提

- 归档签名、索引范围及必要的配套索引已核对。

### 已验证步骤

- 用首条偏移区分记录布局，核对零槽过滤、成员范围及独立 LZSS 样本。

### 限制与失效条件

- 仅记录归档和逻辑成员检查。脚本语义、封包和游戏内加载仍需独立验证。

原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。
<!-- EXPERIENCE:536f2cee8f3e4e33f43b43af3e263da624e68fc4f5c3e407a5b2850f99936dc7:END -->
