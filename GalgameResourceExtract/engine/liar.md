# Liar-soft / RScript：XFL 与 GSC

## 解包与封包工具

| 工具与来源 | 解包用途 | 封包用途 | 适用范围与限制 |
| --- | --- | --- | --- |
| [GARbro Mod CLI](../commands/garbro.md)，随附 | 读标准 XFL，提取 GSC、WCG、LWG 等逻辑成员 | Mod CLI 只读。[兼容后端](../commands/garbro-legacy.md)提供平面 XFL 写入。 | 原版 FVR 的标准 XFL 通过实测。未知头的同后缀汉化包须单独验证。 |
| 外部 [LiarsoftTool v2.3.1](https://github.com/Love-in-idleness/LiarsoftTool/releases/tag/v2.3.1)，GPL-3.0 | GSC 转 TSC 或可翻译文本，保留姓名、选项、命令和标签 | TSC 可编译为独立 GSC 副本 | 已核对两套 FVR 原版的脚本名与局部标签，代表脚本重导的结构一致。 |

## 格式特征与编码方式

| 层级 | 识别与验证 |
| --- | --- |
| XFL | 签名为 `LB 01 00`。索引有定长名称、相对正文区的偏移和存储长度；所引实现对同签名的嵌套 XFL 递归读取。 |
| GSC | 解包获得二进制 GSC。字符串表、指令、控制信息以及文本字符集需按实际脚本版本再解析。 |
| WCG 与 LWG | WCG 是图像编码，LWG 包可关联多个图层与坐标。保留原成员和相对路径，图层语义须另行核对。 |

标准 XFL 解包后可直接对原样 WCG 抽样解码成 PNG，并校验尺寸与哈希。单张 WCG 与 LWG、蒙版或叠层的关系需要配套脚本或图层坐标证据，解包器的平面输出只证明单张图像可读。

## 注意事项

标准索引可独立核验文件名、偏移、长度与样本字节。遇到非标准头的补丁包，先另行识别包层，不把已解包的原版成员当作汉化资源。

### 从原样 GSC 导出脚本

下载固定版 CLI 后核对发布页的 `SHA256SUMS`。Windows 上若路径转换失败，可将输入放在独立的 ASCII 工作路径，输出到新的目录。

```text
liarsofttool -e cp932 -j 1 --gsc-to-tsc "RAW/*.gsc" -o TSC_OUTPUT_DIR
liarsofttool -e cp932 -j 1 --gsc-to-txt "RAW/*.gsc" -o TXT_OUTPUT_DIR
liarsofttool --inspect-tsc INPUT.tsc
```

按输入、两种输出的基名集合核对覆盖。TSC 的 `*TXT` 含说话人和文本两个字符串，`*TXA` 为续接文本。分别统计命令和文本，不把命令数当作最终显示消息数。对 `*jz`、`*jnz`、`*goto`、`*select` 的字面量代码目标逐一比对同脚本标签。跨脚本跳转、表达式和实际存档需另验。编译后可再次导出比对结构；已实测重编译可能改变原生字节。

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

<!-- EXPERIENCE:732d5f15a8eac64a2cca45afd1bee4eb9dfb1e1eb48ebf862a18a29fe13b71c9:START -->
## 双格式导出 GSC 并核对显式姓名和局部标签

- 引擎版本：GSC / LiarsoftTool v2.3.1
- 方言/条件：Windows，限匹配脚本布局
- 阶段：extract
- 验证等级：real_sample
- 经验 ID：`732d5f15a8eac64a2cca45afd1bee4eb9dfb1e1eb48ebf862a18a29fe13b71c9`

本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。

### 适用前提

- 先确认已解包标准归档和实际脚本编码。

### 已验证步骤

- 逐文件核对 TXT 与 TSC 覆盖，并逐一复核 TSC 中的局部字面量目标；用代表脚本重编译再导出检查结构。

### 限制与失效条件

- 只验证匹配 GSC 版本；重编译字节可能不同，跨脚本条件、存档和非标准归档另验。

原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。
<!-- EXPERIENCE:732d5f15a8eac64a2cca45afd1bee4eb9dfb1e1eb48ebf862a18a29fe13b71c9:END -->
