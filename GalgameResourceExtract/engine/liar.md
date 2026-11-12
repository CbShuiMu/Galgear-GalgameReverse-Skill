# Liar-soft / RScript：XFL 与 GSC

## 解包与封包工具

| 工具与来源 | 解包用途 | 封包用途 | 适用范围与限制 |
| --- | --- | --- | --- |
| [GARbro Mod CLI](../commands/garbro.md)，随附 | 读标准 XFL，提取 GSC、WCG、LWG 等逻辑成员 | Mod CLI 只读。[兼容后端](../commands/garbro-legacy.md)提供平面 XFL 写入。 | 原版 FVR 的标准 XFL 通过实测。未知头的同后缀汉化包须单独验证。 |

## 格式特征与编码方式

| 层级 | 识别与验证 |
| --- | --- |
| XFL | 签名为 `LB 01 00`。索引有定长名称、相对正文区的偏移和存储长度；所引实现对同签名的嵌套 XFL 递归读取。 |
| GSC | 解包获得二进制 GSC。字符串表、指令、控制信息以及文本字符集需按实际脚本版本再解析。 |
| WCG 与 LWG | WCG 是图像编码，LWG 包可关联多个图层与坐标。保留原成员和相对路径，图层语义须另行核对。 |

## 注意事项

标准索引可独立核验文件名、偏移、长度与样本字节。遇到非标准头的补丁包，先另行识别包层，不把已解包的原版成员当作汉化资源。

格式参见[固定版 XFL 实现](https://github.com/crskycode/GARbro/blob/102d19710c819ed363b7ea28f2d883ccaf922214/ArcFormats/Liar/ArcXFL.cs)与[LiarsoftTool 源码](https://github.com/Love-in-idleness/LiarsoftTool/tree/619b680741e2baedb7409ed4efb21aa95dd483b7)。

<!-- EXPERIENCE:7b3e545fe71fd9697d1ed239e945c84ac17bd6abca9fe1bf71931b21bd9891b9:START -->
## 按 XFL 索引界定逻辑成员及嵌套范围

- 引擎版本：LB 01 00 XFL
- 方言/条件：Windows 真实样本，限匹配的归档布局
- 阶段：extract
- 验证等级：real_sample
- 经验 ID：`7b3e545fe71fd9697d1ed239e945c84ac17bd6abca9fe1bf71931b21bd9891b9`

本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。

### 适用前提

- 归档签名、索引范围及必要的配套索引已核对。

### 已验证步骤

- 用固定版 GARbro Mod 提取，独立核对标准索引中的成员范围与代表字节。

### 限制与失效条件

- 仅记录归档和逻辑成员检查。脚本语义、封包和游戏内加载仍需独立验证。

原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。
<!-- EXPERIENCE:7b3e545fe71fd9697d1ed239e945c84ac17bd6abca9fe1bf71931b21bd9891b9:END -->
