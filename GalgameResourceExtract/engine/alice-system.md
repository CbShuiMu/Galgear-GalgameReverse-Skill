# AliceSoft System 4：AFA、ALD 与 AIN

## 解包与封包工具

| 工具与来源 | 解包或读取 | 封包 | 适用范围 |
| --- | --- | --- | --- |
| 随附 [GARbro Mod](../commands/garbro.md) | 读 AFA 与 ALD，抽提成员并解码代表图像 | 未验证 | 分别核对两种索引 |
| 外部 [alice-tools 0.12.0](https://github.com/nunuhara/alice-tools/releases/tag/0.12.0) | 解析 AIN 版本、函数、消息与字符串 | 本轮未验证 | 核对当前安装的输入编码 |

## 格式特征与编码

经典 AFA 从 `AFAH` 和 `AlicArch` 识别，随后按 `INFO` 核对压缩索引。ALD 按索引范围与成员位置判断。AFA 的 AFF 分支可能剥除包裹并还原成员头。QNT、AJP、Ogg 与解包后的 SWF 分别按签名确认。

`AI2` 是 AIN 压缩包装的候选特征。用工具核对 AIN 版本和段结构，再用适用编码导出。实测 AIN v6 汉化样本可用 CP936 导出，CP932 报非法字节序列。对不同安装重新验证。

## 全量成员核验与 AFA 静态往返

对 AFA、ALD 分别列索引，按条目序号保存成员，核对路径、范围、输出长度和 SHA-256。AFF 展开后的媒体头单列。对经核实的 AFA，可用 alice-tools 的 ALICEPACK 清单重建，再用独立读取器逐项核对相对路径与逻辑成员。在已验证的小型样本中，索引布局变化时内容及路径仍可逐项一致。成员名称编码或原有包装不同的归档继续按当前输入复测。

## 文本定位

用 `alice ain dump --input-encoding ENCODING --output-encoding UTF-8 --text -o OUTPUT INPUT` 导出按函数组织的消息和字符串。用 `--functions` 核对函数表，保留 `m[ID]` 和 `s[ID]`，分别统计去重 ID 和静态引用次数。函数坐标仍需结合指令和调用关系才能确认说话人、分支或实际存档位置。 [AIN 工具文档](https://haniwa.technology/alice-tools/README-ain.html)

<!-- EXPERIENCE:1814e9a615096abc8bab72c779583f322caf62510f4163dd3f06748249348bd6:START -->
## 归档成员与本地化 AIN 分层导出

- 引擎版本：AFA / ALD / AIN v6
- 方言/条件：Windows 安装实测，以固定版本及样本的边界检查为准
- 阶段：extract
- 验证等级：real_sample
- 经验 ID：`1814e9a615096abc8bab72c779583f322caf62510f4163dd3f06748249348bd6`

本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。

### 适用前提

- 有 AFA、ALD 归档索引及实际 AIN 版本证据

### 已验证步骤

- 固定版 Mod 核对目录及样本头。用 alice-tools 0.12.0 验证输入编码，导出 UTF-8 消息和函数坐标

### 限制与失效条件

- 代表成员验证不等同于全包载荷，函数坐标不能代替分支和说话人分析

原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。
<!-- EXPERIENCE:1814e9a615096abc8bab72c779583f322caf62510f4163dd3f06748249348bd6:END -->
