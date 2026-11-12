# rUGP / RIO：图像载荷与累计 RUO

## 解包与封包工具

| 工具、来源 | 解包用途 | 封包用途 | 版本与限制 |
| --- | --- | --- | --- |
| 随附 AgeReVerse RIO 目录 CLI | ICI／RIO 对象类、卷内位置及范围 | 不提供目录写入 | 固定提交 `17618428499e90aa9b971212f7167cfdaf09912b`，MIT；[目录命令](../commands/age-rio.md) |
| 随附 [CRsa 脚本载荷 CLI](../commands/rugp-crsa.md) | 对目录中的 CRsa 按卷内范围保留原始记录与解密后的 VM 载荷 | 只读 | 11 和 12 字节对象头均有真实样本；完整块和末尾短块都校验 |
| 随附 rUGP 图像／RUO CLI | 标准 Cr6Ti、已实现 CRip008 子集的原样资源和 PNG | Cr6Ti 编码及累计 RUO 的静态字节／像素读回 | [命令与源码](../commands/rugp-images.md)；真实样本验证，不包含安装或游戏运行通过声明 |
| GARbro Mod 1.0.2.2 | 常见 RIO 的候选读取路线 | 不支持 RIO 写入 | 当前真实 RIO 仍报 unknown format；不能仅看退出码 0 |
| Windows Installer 只读数据库与 Cabinet FDI | 定位安装介质中的 RIO、媒体和其他安装文件，按 CAB 卷链提取 | 当前路线只读 | Windows 外置多卷 CAB 实测。内部 RIO 对象目录仍需匹配读取器 |
| 外部 [oor-extractor][oor] 与 [vgmstream CLI][vgm] | 按卷扫描 OOR 流；另存原样音频和可用的元数据；抽样转 WAV | 当前路线只读 | 固定版真实样本验证，按卷内范围逐条比对，语音身份与对白引用另验 |

## 格式特征与编码方式

ICI／对象目录、图像记录及 RUO 重定向分别处理。目录没有列出所有被加载图像时，可以对保留原件做有边界的载荷扫描，但扫描身份必须与目录身份分开；名称未恢复时以来源、全局／卷内偏移、精确范围和哈希追溯，不编造名称或把匹配头当成完整 CG 清单。

对 CRsa 先确认目录指向的对象类型与卷内范围，再按对象头确定加密块起点。真样本出现 11 字节与 12 字节两种头，两者使用同一分块校验流程。两处长度声明需一致，并核对最后一个短块的校验和与整个目录范围。物理扫描找到的脚本只保留偏移身份；台词、姓名、语音映射和剧情流程以 VM 证据另验。[AgeReVerse CRsa 实现][crsa]

标准 Cr6Ti 与 CRip008 共有 `00 04 45`。前者按已识别 profile 核对 0x2C 字节头、载荷长度和两个零尾字节，后者长度位置及头长度不同。对齐填充不是记录范围。调色、透明度和压缩码流与归档偏移编码分别验证；Cr6Ti kind 3 保留画布、绘制矩形、偏移和量化 alpha。

RUO 为数据区、每项三个 uint32 的重定向表及末尾条目数，使用当前归档的偏移／范围编码和分配单位。分配单位须由当前 ICI 和已有 RUO 证明，不能跨版本照搬。已有 RUO 的基线数据和未修改重定向保持不变，生成一份累计副本；它不是完整 RIO／ICI 重建器，也没有新增任意逻辑路径的支持。

读取已有 RUO 时保留原表顺序。真实样本的表项未按有符号或无符号源键排序；可独立核对键唯一性、目标范围及数据区与尾表的边界。用物理扫描发现的内部记录必须再与重定向目标范围核对。

目录可能未列出音频。对已识别的 OOR 流，可在每卷的独立输出目录运行 `oor-extractor -v -b member INPUT`，并记录提取器报告的卷内偏移及长度。用这些字段从原卷逐条读回比较，分别清点流及元数据；再用 vgmstream 验证代表性流的采样率、声道、长度和 PCM 读回。音频身份、引用和跨卷拼接另验。

## 已验证子集与失效条件

对于以 MSI 安装介质分发的样本，先用 [Windows Installer 只读数据库][msi-open]查询 [Media 表][msi-media]与 File 表。外置 CAB 按介质序列排列，内部成员名对应 File 主键。核对各 CAB 的 set ID、卷序号、连续项与声明长度后，从每个 CAB 卷首依次调用 [FDICopy][fdi]。只接受已列入 Media 表的续卷和已列入 File 表的输出。跨卷文件可在前一卷的调用中完成，后续调用复用同一输出清单，避免重复计数。以 File 键、声明长度及输出哈希核验；原版和更新包分别保留。仅运行 `expand.exe` 在当前实测中会停在跨卷成员。安装层完成后再按 RIO 版本匹配对象目录和资源读取器。

真实样本已验证原生记录提取、Cr6Ti／CRip008 已支持 profile 的逐条解码，以及 Cr6Ti 未修改和受控修改的静态累计 RUO 往返。返回 PNG 不足以验收：旧 Cr6Ti v1 的 kind 3 在共享差值／残差分步钳位以及透明段后的预测状态上与 native reference 不同。当前适配使用严格封装检查加 native reference；相关合成回归覆盖颜色越界后钳位和透明上一行的清除。

编码器自己的“expected pixels”不等于输入像素。默认要求独立读回与输入全部相同；未变化的图像保留原生字节，有损候选只有明确选项才允许生成。原版、汉化包及已有 RUO 保持来源；不根据相似图像删除差分，不把子图或 UI 数当作独立 CG 数。

仍未验收：完整 CG／图库与脚本引用覆盖、CBg2d 等未实现的类、所有父对象叠放规则、任意图片的无损重编码、完整 RIO 重建，以及实际游戏对新 RUO 的加载和显示。静态往返产物不自动获得安装许可。逐款范围见 [CG 实测状态](../catalog/cg-status.md)。

[msi-open]: https://learn.microsoft.com/en-us/windows/win32/api/msiquery/nf-msiquery-msiopendatabasew
[msi-media]: https://learn.microsoft.com/en-us/windows/win32/msi/media-table
[fdi]: https://learn.microsoft.com/en-us/windows/win32/api/fdi/nf-fdi-fdicopy
[crsa]: https://github.com/RepressedAlliance/AgeReVerse/blob/17618428499e90aa9b971212f7167cfdaf09912b/rUGP/formats/rio/crsa.py
[oor]: https://github.com/bnnm/vgm-tools/tree/0952e175883747c64ca69faf3a7635d96ec243fa/misc/oor-extractor
[vgm]: https://github.com/vgmstream/vgmstream/releases/tag/r2168

<!-- EXPERIENCE:d82cadd83110f97dcd09141089155c7e4b176cb3a484714351713ee9c1b56273:START -->
## 严格读取原生图像、透明差分与像素身份

- 引擎版本：Standard Cr6Ti kind2/3 and supported CRip008; AgeReVerse 17618428499e90aa9b971212f7167cfdaf09912b
- 方言/条件：Bounded static image and cumulative RUO work; native-reference kind3 semantics
- 阶段：extract
- 验证等级：real_sample
- 经验 ID：`d82cadd83110f97dcd09141089155c7e4b176cb3a484714351713ee9c1b56273`

本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。

### 适用前提

- 先核对头、精确范围、当前分配单位与输入哈希；扫描候选身份和目录身份分开记录
- 标准记录与已实现 profile 匹配；已有覆盖包作为完整基线保留

### 已验证步骤

- 保留每份来源的原生字节，以来源／偏移／范围／哈希定位，不按名称或相似度丢弃差分
- 使用严格封装检查及 native reference；kind3 在残差后钳位并清除透明预测状态
- 编码默认拒绝输入像素误差；保留未修改记录字节；累计写入后检查 footer、载荷及全部目标像素

### 限制与失效条件

- 只证明所列 profile 的图像与静态封装阶段；完整 CG／图库、父对象组合与逻辑名称未还原
- CBg2d 及未知 profile 不猜测解码；任意修改图像不保证可无损编码
- 完整 RIO／ICI 重建、安装、新 RUO 实际加载及游戏显示未验收；项目数据只保存在本地

原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。
<!-- EXPERIENCE:d82cadd83110f97dcd09141089155c7e4b176cb3a484714351713ee9c1b56273:END -->

<!-- EXPERIENCE:20ba418313cd16d46f2bcfd0a147076f844a84f29ef74840040d724d79a1626f:START -->
## 按 MSI File 主键校验跨卷 CAB 安装层

- 引擎版本：MSI external cabinet set / Windows FDI
- 方言/条件：Windows 真实样本，限所列的读取层及布局
- 阶段：extract
- 验证等级：real_sample
- 经验 ID：`20ba418313cd16d46f2bcfd0a147076f844a84f29ef74840040d724d79a1626f`

本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。

### 适用前提

- 只读查询 MSI Media 与 File 表，核对 CAB 组号、序列、成员主键、长度和续卷。

### 已验证步骤

- 通过 Cabinet FDI 从各卷依次展开，限制到表内成员及续卷，将产物逐项核对 File 键、长度和哈希。

### 限制与失效条件

- 只验证 MSI/CAB 安装层。内层 RIO 对象目录、CG 和封包按目标版本另验。

原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。
<!-- EXPERIENCE:20ba418313cd16d46f2bcfd0a147076f844a84f29ef74840040d724d79a1626f:END -->

<!-- EXPERIENCE:1f1481a744954565c7b235ec221f41f8775bf86db0a2f3b3b7007f01278098e8:START -->
## 从两种对象头读取 CRsa 并校验末尾短块

- 引擎版本：CRsa / 11- and 12-byte object headers
- 方言/条件：Windows 真实样本，限所列的读取层及布局
- 阶段：extract
- 验证等级：real_sample
- 经验 ID：`1f1481a744954565c7b235ec221f41f8775bf86db0a2f3b3b7007f01278098e8`

本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。

### 适用前提

- 通过 ICI 对象类及精确卷内范围确认 CRsa 记录。

### 已验证步骤

- 分别核对头部、双长度字段、完整块和短块校验。原样记录与解密载荷分开保存，用独立读取结果逐字节比对。

### 限制与失效条件

- 只确认已匹配的脚本载荷；目录外身份、VM 语义、封包和游戏内加载仍需独立验证。

原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。
<!-- EXPERIENCE:1f1481a744954565c7b235ec221f41f8775bf86db0a2f3b3b7007f01278098e8:END -->

<!-- EXPERIENCE:c6622085dff24a35228b32d269e7b560bd914fce37b6abbd4b4d15ddab8bbe6a:START -->
## 按 RIO 分卷提取 OOR 并以源范围和 WAV 验证

- 引擎版本：OOR / oor-extractor 0952e1758837 / vgmstream r2168
- 方言/条件：Windows 真实样本，限所列的读取层及布局
- 阶段：extract
- 验证等级：real_sample
- 经验 ID：`c6622085dff24a35228b32d269e7b560bd914fce37b6abbd4b4d15ddab8bbe6a`

本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。

### 适用前提

- 保留原卷、独立输出和提取器报告的卷内范围。

### 已验证步骤

- 独立逐条核对源字节和输出哈希。按来源抽取代表性文件转 WAV，检查声道、采样率和 PCM 长度。

### 限制与失效条件

- 音频名、脚本引用、覆盖优先级、跨卷流与完整语音覆盖均须另验。

原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。
<!-- EXPERIENCE:c6622085dff24a35228b32d269e7b560bd914fce37b6abbd4b4d15ddab8bbe6a:END -->
