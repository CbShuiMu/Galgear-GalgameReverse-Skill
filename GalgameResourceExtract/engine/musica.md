# MUSICA：PAZ 方案与逻辑成员

## 解包与封包工具

| 工具与来源 | 解包用途 | 封包用途 | 适用范围与限制 |
| --- | --- | --- | --- |
| [序号解包 CLI](../commands/garbro-archive.md)与随附 GARbro Mod | 从当前数据库显式选 PAZ 方案，读取索引和成员 | 所引读取路线无写入接口 | 已用两套运行库对照真实 PAZ 脚本包字节。 |
| [parse_musica_sc.py](../scripts/parse_musica_sc.py) | 提取 SC 台词、说话人、语音引用与字面量控制流 | 只读 | 已核对原版、附加包和汉化脚本的字段及目标坐标。 |

## 格式特征与编码方式

PAZ 索引偏移和处理由所选方案版本决定。归档文件名可参与方案内的分包参数查找。原版、附录、平台再版或改名补丁可能需要不同条目，不能因为前三个字节或后缀相同就共享参数。文件名、索引变换、压缩和脚本语法分别核对。

自动 CLI 识别失败后，先查随附运行库的方案名及适用包名。显式选择后检查索引路径、偏移和长度，再核对脚本结构、媒体签名和输出哈希。多个方案都能列出时，以合法成员载荷作进一步证据。记录数据库版本和失败包；专用参数留在本地。

来源为[固定版读取实现](https://github.com/crskycode/GARbro/blob/102d19710c819ed363b7ea28f2d883ccaf922214/ArcFormats/Musica/ArcPAZ.cs)。

## SC 台词、条件与场景引用

```text
python scripts/parse_musica_sc.py INPUT_SC_DIR NEW_REPORT.json
python scripts/parse_musica_sc.py LOCALIZED_SC_DIR NEW_REPORT.json --text-encoding gbk --speaker-encoding cp932
python scripts/parse_musica_sc.py ADDON_SC_DIR NEW_REPORT.json --chain-base BASE_SC_DIR
python scripts/trace_musica_sc.py BASE_SC_DIR ENTRY.sc NEW_ROUTE.json --initial FLAG=0
```

每次传入一组平铺的原样 SC 成员。按单个空格或制表符切出 `.message` 的消息号、语音引用、姓名和正文，保留空字段、重复消息号、原始行号和字节偏移。说话人前缀 `@` 单独保留，语音引用保留原值，包括方括号参数。正文里的控制转义保留原样。汉化样本的正文和姓名采用不同编码，先用同场景、消息号、语音引用与同号出现次序和原版对齐，再指定编码。[固定版 SC 字段参考](https://github.com/arcusmaximus/VNTranslationTools/blob/36fbe909d02f2e9bb187443e03e2df595f56bfec/VNTextPatch.Shared/Scripts/MusicaScript.cs)

`.if` 输出条件、字面量标签和顺序后继，`.goto` 核对同文件标签，`.chain` 切换到目标 SC，`#include` 在当前路径中引入脚本并保留返回点。已确认配套原版目录时，可用 `--chain-base` 核对缺失的文件目标。输出标注目标来源与基组文件哈希。

路线工具支持显式整数赋值、整数比较、标签、切换及嵌入。用 `--overlay` 显式提供已核对的同名覆盖源。逐条输出走到的台词、原始文件和坐标，遇到缺失标志或未支持的控制命令时报告位置。保留 `.set`、`.setGlobal` 和 `.pragma` 供核对状态写入和存档开关。运行时菜单、读取槽位及实际恢复仍需独立证据。

PAZ 的 `mov` 包名还可能改变索引布局和成员解码器。前缀改名的包可用独立工作目录中的同名副本对照。索引可读时，继续检查成员长度、预期内容结构与资源身份，再确定提取状态。[固定版 PAZ 读取器](https://github.com/crskycode/GARbro/blob/102d19710c819ed363b7ea28f2d883ccaf922214/ArcFormats/Musica/ArcPAZ.cs)

<!-- EXPERIENCE:b82d8506ba722b045ac660280bf8624a97cec0432e5d355ece82c71102280775:START -->
## 显式选择 PAZ 读取方案并逐哈希对照逻辑脚本成员

- 引擎版本：PAZ scheme version 1
- 方言/条件：Windows 真实样本，限已核对的读取范围
- 阶段：extract
- 验证等级：real_sample
- 经验 ID：`b82d8506ba722b045ac660280bf8624a97cec0432e5d355ece82c71102280775`

本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。

### 适用前提

- 用真实源文件和验证结果确认当前版本与读取层级。

### 已验证步骤

- 用运行库数据库中的匹配名称选择方案。以两套独立运行目录解包并对照全清单和输出字节。

### 限制与失效条件

- 仅限与已验证方案匹配的归档；索引、逻辑载荷与脚本消费者分别验证。

原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。
<!-- EXPERIENCE:b82d8506ba722b045ac660280bf8624a97cec0432e5d355ece82c71102280775:END -->

<!-- EXPERIENCE:342936cf5cd9d6fde67ebb6128806761b876cb811d079c3234d41b8e3dc21c8a:START -->
## 保留 SC 消息字段与位置并验证字面量控制流

- 引擎版本：MUSICA SC
- 方言/条件：Windows，限匹配脚本布局
- 阶段：extract
- 验证等级：real_sample
- 经验 ID：`342936cf5cd9d6fde67ebb6128806761b876cb811d079c3234d41b8e3dc21c8a`

本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。

### 适用前提

- 使用已验证的逻辑脚本成员，明确正文和姓名编码。

### 已验证步骤

- 按单个分隔符切出消息字段，用原始字节复核位置、姓名及正文；以标签和源组匹配字面量目标。

### 限制与失效条件

- 仅匹配 SC 语法，存档槽位、实际条件求值及语音文件对应关系另验。

原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。
<!-- EXPERIENCE:342936cf5cd9d6fde67ebb6128806761b876cb811d079c3234d41b8e3dc21c8a:END -->
