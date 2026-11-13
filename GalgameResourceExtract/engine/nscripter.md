# NScripter：SAR / NSA / NS2 与脚本

本页按归档布局识别，不把扩展名或 ONScripter 兼容性当作所有 NScripter 版本的证明。ONScripter 的分支与编码另见 [ONScripter](onscripter.md)。

## 解包与封包工具

| 工具与来源 | 解包或读取用途 | 封包或重建用途 | 适用范围与限制 |
| --- | --- | --- | --- |
| [GARbro Mod CLI](../commands/garbro.md)，随附；[SAR][sar] / [NSA][nsa] / [NS2][ns2] 源码 | 读取支持的 SAR、NSA、NS2，NSA 可解开 SPB / LZSS / NBZ 成员 | Mod CLI 不提供封包；需另选匹配的引擎工具 | NS2 在此写入器中 `CanWrite=false`；NSA 不写 SPB / NBZ 或密码保护。不能用改扩展名代替 NS2 封包 |
| [GalArc CLI](../commands/galarc.md)，随附适配工具 | 标准 NS2 归档读取能力以对应命令和合成测试为准 | 用于补齐标准 NS2 创建 | 只使用文档已列并验证的格式，不把上游 GUI 的全部能力当作 CLI 能力；特殊加密与变体另核对 |
| [ONScripter-Tools][ons-tools]，外部 GPL 工具参考 | `nscdec` 处理支持的 `nscript.dat` 脚本包装；`nsadec`、`ns2dec`、`sardec` 处理对应归档 | `nscmake` 创建脚本包装；`nsamake`、`ns2make`、`sarmake` 创建对应归档 | 本技能未随附这组工具；工具分支和脚本包装必须匹配。`nscript.dat` 的编解码不是资源归档解包 |

## 格式特征与编码方式

| 层级 | 通用识别特征 | 编码或变换方式与判定依据 |
| --- | --- | --- |
| SAR | 通常没有固定魔数；开头为大端文件数和数据起点，索引为 NUL 结尾名称、相对偏移及长度 | 所引 GARbro 读写名称使用 CP932；先校验索引、数量及数据范围，不能只靠 `.sar` 识别 |
| NSA | SAR 类头部与索引；条目另含压缩类型、存储长度和原始长度 | 多字节字段使用大端。名称按同版本工具的 CP932 规则处理；压缩类型 0 / 1 / 2 / 4 分别对应原样 / SPB / LZSS / NBZ，见[NSA 实现][nsa] |
| NS2 | 所引标准布局以小端数据起点开头，随后是双引号括起的名称与小端长度，成员连续排列 | 名称读取器使用 CP932；与 NSA 的大端偏移索引不同，没有 NSA 式逐条压缩标记。确认布局后选写入器，不能套用 NSA 参数 |
| 脚本文字 | `0.txt`、编号 TXT 或被包装的 `nscript.dat`；文件名不等于文字编码声明 | 先还原包装，再核对目标版本字符读取器。日文兼容读取通常使用 CP932，UTF-8 或其他分支必须有明确版本/配置证据；不能因一份汉化文本可读便更改通用规则 |
| 脚本包装 | [ONScripter 兼容实现][script]对标准 `nscript.dat` 使用逐字节 XOR `0x84` | XOR 是可逆包装，不是字符编码。其他安全脚本包装与密钥表由目标读取实现确认，不用 `0x84` 通试所有 DAT |
| 内部媒体 | SPB 为图像压缩，NBZ 使用长度字段与 bzip2 压缩，可承载图像或音频 | 解包后按成员真实文件头核对 BMP、WAV、Ogg、MP3 等；不按扩展名推断所有 NBZ 都是音频，不因归档使用 CP932 就转码媒体 |

## 注意事项

- NSA 的 `ns2` / `ns3` 命令所表示的前置字节偏移与 `.ns2` 归档布局是不同概念。[兼容读取实现][reader]分别处理这两者；不要看到命令名就选择 NS2 封包。
- 分别保留每个归档的原样资源根目录和条目清单；散文件、补丁归档及多卷加载优先级由项目配置确认。改变文件名大小写、目录或文字编码可能破坏实际引用。
- GARbro 会解开 NSA 压缩成员。封包比较解包后的成员语义与字节，不要求压缩后的归档逐字节相同；需要保留原压缩方式却没有相应写入能力时，明确报告缺口。
- 封包后重新解包并比较完整路径、数量及哈希；脚本包装往返、脚本命令语义和游戏加载分别验证。

## 来源、版本与验证边界

归档依据 GARbro `b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0` 与 ONScripter `848a60892e4d721459e8d1051e1b8fe45164c3e9` 的读取实现；外部工具说明固定为 ONScripter-EN-Steam `c28bb8b383addac76413027d0bd9360a0834d973`。这些是实现参考，不是原版 NScripter 的完整格式规范；NS2 适配工具验证等级另见命令页。没有真实游戏或运行验证；索引、编码、压缩类型或脚本包装与来源不符时停止套用。特殊密钥和游戏内容留在用户本地。

[sar]: https://github.com/morkt/GARbro/blob/b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0/ArcFormats/NScripter/ArcSAR.cs
[nsa]: https://github.com/morkt/GARbro/blob/b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0/ArcFormats/NScripter/ArcNSA.cs
[ns2]: https://github.com/morkt/GARbro/blob/b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0/ArcFormats/NScripter/ArcNS2.cs
[reader]: https://github.com/ogapee/onscripter/blob/848a60892e4d721459e8d1051e1b8fe45164c3e9/SarReader.cpp
[script]: https://github.com/ogapee/onscripter/blob/848a60892e4d721459e8d1051e1b8fe45164c3e9/ScriptHandler.cpp
[ons-tools]: https://github.com/GoldbarGames/ONScripter-EN-Steam/blob/c28bb8b383addac76413027d0bd9360a0834d973/tools/readme.txt

## CG 与差分图像（实测子集）

从已识别的 NSA 图像成员保留原生文件并另存 PNG；不把背景、角色立绘和按钮算成已确认事件 CG。 实际样本阶段见 [CG 状态表](../catalog/cg-status.md)，命令与边界见 [图像 CLI](../commands/garbro-images.md)。本节不声明完整 CG 或全部差分组合。

<!-- EXPERIENCE:c594f19e4b5b730ab39870370f6dd20d1c7225bbb1c0c7192ed815ca597ac6df:START -->
## 已验证脚本子集提取；脚本坐标与存档恢复分别验收

- 引擎版本：当前真实样本；版本兼容性未扩展
- 方言/条件：Windows 静态提取；不验证运行时
- 阶段：extract
- 验证等级：real_sample
- 经验 ID：`c594f19e4b5b730ab39870370f6dd20d1c7225bbb1c0c7192ed815ca597ac6df`

本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。

### 适用前提

- 文件头与实际读取器匹配；先列出条目并验证边界
- 工具输出需核对条目名称、大小和层级

### 已验证步骤

- 历史验证使用 GARbro CLI 0.1.1.0（现已移除，改用 Mod 后须重验） / SSSU 0.5.7 / rlseen 1.0 或标准 NScripter XOR 包装路线，实际调用见本地报告
- 保存输入身份、成员清单、脚本副本和独立验证结果；原游戏保持不变

### 限制与失效条件

- 只证实当前样本提取阶段；不证明其他版本、补丁覆盖顺序、完整台词、存档恢复或封包兼容性
- 静态标签和候选命令不是实际存档槽位；无运行时验证

原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。
<!-- EXPERIENCE:c594f19e4b5b730ab39870370f6dd20d1c7225bbb1c0c7192ed815ca597ac6df:END -->

<!-- EXPERIENCE:42ccbcc2759b0a37714cfc1e074e2f188b9aa0801e4adc5889e04e1ad0539014:START -->
## 已验证脚本逆变换与显示行候选坐标；宏及动态状态未展开

- 引擎版本：NScript XOR84
- 方言/条件：Windows offline; explicit format checks; no runtime save loading
- 阶段：extract
- 验证等级：real_sample
- 经验 ID：`42ccbcc2759b0a37714cfc1e074e2f188b9aa0801e4adc5889e04e1ad0539014`

本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。

### 适用前提

- 确认容器与成员身份，保留原件及独立来源；复用前检查SHA-256
- 当前脚本布局必须符合对应读取器，字符编码由项目证据显式指定

### 已验证步骤

- 逐文件读取并保留原生坐标、消息分类、姓名来源与失败诊断；解析器不执行游戏脚本
- 本地Python适配器及固定版本VNTranslationTools v0.0.41、SSSU 0.5.7、unrpyc 2.0.3按格式分流，实际实现、来源和命令留在本地
- 独立核对导出计数、唯一ID、来源哈希与已知坐标边界；支持的布局另对代表性脚本重新解析核对

### 限制与失效条件

- 只覆盖本次成功子集；具体失败项和数量保存在本地，不能扩展为全引擎支持
- 未确认全路线剧情、补丁覆盖顺序、未知控制指令、语音关联或实际存档恢复
- 语言键、文件顺序与字符串顺序不能自动证明正文语言或运行顺序；原生坐标和候选关联分别保存

原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。
<!-- EXPERIENCE:42ccbcc2759b0a37714cfc1e074e2f188b9aa0801e4adc5889e04e1ad0539014:END -->

<!-- EXPERIENCE:382aeea853287285d00ae1960453e6dd4263d5049195a1dd071250fa38cda31a:START -->
## 按源脚本保留标签与字面量目标引用；宏与条件仍未展开

- 引擎版本：NScript XOR84 decoded source; static labels
- 方言/条件：Windows offline source/bytecode refinement; scope limited to passed files
- 阶段：extract
- 验证等级：real_sample
- 经验 ID：`382aeea853287285d00ae1960453e6dd4263d5049195a1dd071250fa38cda31a`

本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。

### 适用前提

- 来源文件与已验证快照一致，逐文件保留格式版本、字符编码和失败项
- 消费者、操作数、字符串或数据库引用由实际读取实现与样本结构支持，不按文件名猜配

### 已验证步骤

- 使用项目本地Python适配器与固定SSSU 0.5.7 / VNTranslationTools v0.0.41读取实现保留原生坐标，代码和源码证据均留在本地
- 分别输出消息、片段或明确候选，保留姓名字段、语言槽位、分支/引用图的实际证据类型
- 核对来源哈希、记录ID和计数、已知坐标边界及图端点；读取失败或未知版本不计为该阶段成功

### 限制与失效条件

- 部分产物是片段、候选或引用图；统计不代表唯一句数、选择数或所有可达剧情
- 动态指令、未知消费者、补丁覆盖与全路线语义仍有未解决项，具体数量在本地报告
- 缓存命中、存档字段解码和静态坐标一致均不等于游戏内加载验证；没有运行时恢复成功声明
- 项目专用编码、列号、消费者编号、布局特例和原游戏内容不写入随包通则

原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。
<!-- EXPERIENCE:382aeea853287285d00ae1960453e6dd4263d5049195a1dd071250fa38cda31a:END -->

<!-- EXPERIENCE:de8335df4539792fe4a6aa9caaffaca9486a8af203f94d9f63b037f61eb69fc9:START -->
## 图像原生资源与解码副本分别保留并核验；差分、子图与未完成项独立记录

- 引擎版本：Matched local image layouts; GARbro/GameRes 1.5.44 or recorded external reader
- 版本迁移限制：本条保留历史验证版本；旧运行库现已移除，当前 GARbro Mod 必须重新核对。
- 方言/条件：Read-only image extraction substage; no complete CG claim
- 阶段：extract
- 验证等级：real_sample
- 经验 ID：`de8335df4539792fe4a6aa9caaffaca9486a8af203f94d9f63b037f61eb69fc9`

本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。

### 适用前提

- 来源签名、索引与读取器匹配；不同归档和补丁保持独立目录
- 单个原生图像、配套层或子图身份可追溯，未将图片数量视为独立 CG 数

### 已验证步骤

- 在独立工作目录提取所选原生图像；记录来源、位置、大小与 SHA-256
- 按匹配读取器另存 PNG 和多子图，保留偏移及错误／延期，不覆盖原生文件
- 逐文件核对已登记输出哈希、大小与 PNG 尺寸；只声明本轮成功子集

### 限制与失效条件

- 图像候选包含背景、立绘、UI、子图和不同分包；完整 CG 语义未验收
- 预算延期、未知编码、同名条目、配套层和实际补丁加载仍有单独限制
- 没有游戏内视觉组合、全部差分或封包回写成功声明；原图片及用户路径只留本地

原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。
<!-- EXPERIENCE:de8335df4539792fe4a6aa9caaffaca9486a8af203f94d9f63b037f61eb69fc9:END -->
