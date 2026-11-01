# Ren'Py：RPA 归档与 RPY / RPYC 脚本

RPA 是资源容器，RPYC 是编译脚本；解包、脚本反编译、重新编译和资源封包分别验证。

## 解包与封包工具

| 工具与来源 | 解包或读取用途 | 封包或重建用途 | 适用范围与限制 |
| --- | --- | --- | --- |
| 本技能 [locate_renpy_save.py](../scripts/locate_renpy_save.py) 与 passive_pickle 辅助读取器 | 匹配旧 ZIP 日志中的活动 RollbackLog 节点与旧式 zlib RPYC 原生身份 | 不写存档或 RPYC | 不导入 pickle 类或调用 reducer；只支持已测试旧布局，现代 RPYC2 和其他对象操作码未覆盖 |
| [rpatool CLI](../commands/rpatool.md)，随附；[Shizmob 上游][rpatool] + 本地适配 | 标准 RPA v2 / v3，读取全部分段及可选前缀 | 创建 RPA v2 / v3，保留子目录和原始成员字节 | Python 3.9+ 标准库；受限 pickle、大小与路径校验。只验证合成资源，RPI、v3.2、专用混淆不在适配入口范围 |
| [GARbro CLI](../commands/garbro.md)，随附；[RPA 实现][garbro] | 所引读取器仅接受 `RPA-3.0`，每个成员仅使用首个索引片段 | 创建 RPA-3.0，可配置索引 XOR `Key` | 不是全版本或多分段 RPA 读取器；需要完整提取时优先用随附 rpatool，按所有条目检查 |
| [unrpyc][unrpyc]，外部 MIT 工具 | 将支持的 `.rpyc` / `.rpymc` 反编译为脚本工作副本 | 不负责生成 RPYC 或创建 RPA | 未随附；v2 CLI 需 Python 3.9+，旧脚本适配看该版本兼容说明。只选离线 CLI，不自动采用向游戏注入 `un.rpyc` 的路线 |
| [Ren'Py SDK][engine]，外部官方工具 | 读取自己支持版本的脚本与资源 | 从源脚本编译 RPYC，并按发布配置创建 RPA | 不是本技能运行依赖；使用与目标兼容的 SDK。SDK 编译会解释项目初始化代码，须按实际任务授权单独安排，不作为本页测试步骤 |

## 格式特征与编码方式

| 层级 | 通用识别特征 | 编码或变换方式与判定依据 |
| --- | --- | --- |
| RPA v2 / v3 | ASCII 头 `RPA-2.0 ` / `RPA-3.0 `，带十六进制索引偏移；v3 另含 XOR key | 索引为 zlib 压缩的 pickle；v3 对条目偏移和长度做 XOR。XOR 不等于成员加密，归档成员通常原样存储，见[官方 loader][loader] |
| 索引名称与成员 | 索引将成员相对路径映射到一个或多个数据片段，可附前缀字节 | 名称是 Unicode 或兼容 UTF-8 字节；按具体 pickle 数据类型和版本读取。完整成员须拼接所有片段与前缀，不能只读取第一段 |
| RPY 文本 | `game/` 下 `.rpy` 与关联脚本文件；文件边界不代表场景顺序 | 所引官方 [lexer][lexer]按 UTF-8 读取。保留缩进、转义、标签和字符串插值；不要把 RPA 的 ASCII 头当作脚本文字编码 |
| RPYC 编译脚本 | 所引现代格式有 `RENPY RPC2` 头、槽位偏移表及压缩数据；旧格式不同 | 包含 zlib 压缩的序列化脚本结构，不是可直接按 UTF-8 解码的对白；按匹配版本反编译，见[官方 script.py][script] |
| 内部媒体 | RPA 可同时容纳图像、音频、视频及任意项目资源 | 按成员自身文件头和目标 Ren'Py 版本能力判断；RPA 索引压缩不会把 Ogg、WAV 或图像转成某种统一编码 |

## 注意事项

- RPA 索引和 RPYC 都可能含 pickle 数据；不能直接用无限制 `pickle.loads` 解析未知包内对象。随附 rpatool 已替换为受限读取；外部脚本解析器仍须核对它自己的数据处理边界。
- [.rpy 与 .rpyc 加载关系][language]会影响实际脚本：没有相应 `.rpy` 的旧 `.rpyc` 仍可能被加载。基线保留原字节；需要更改或移除旧编译文件时先确认构建规则，不把反编译产物直接混入原样资源根目录。
- 需要对白与语音关联时，分别核对 `voice`、角色定义、自动语音配置及脚本分支；归档文件排列和 RPYC 序列化对象顺序不是阅读顺序。
- 封包后独立解包比对完整路径、数量与哈希；这只能证明资源往返，不能代替反编译准确性、SDK 编译结果或目标加载验证。

## 来源、版本与验证边界

格式依据 Ren'Py `f5c62227489ba60939432f0a33dd7eceb6d83b54` 的 loader / lexer / script 实现；GARbro 固定 `b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0`，rpatool 固定 `74f26d5dfdd645483e02552aa766ca447ad6b191`，unrpyc 参考固定 `3ae8334ed71a05535927dcc559663d3aca51215b`。格式结论是源码阅读等级；随附 rpatool 完成标准 v2 / v3、多片段及前缀的合成 CLI 往返测试，没有真实游戏或运行验证。非标准头、pickle 扩展、编译脚本版本或资源过滤不符时失效，项目参数留在本地。

[rpatool]: https://github.com/Shizmob/rpatool/tree/74f26d5dfdd645483e02552aa766ca447ad6b191
[garbro]: https://github.com/morkt/GARbro/blob/b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0/ArcFormats/RenPy/ArcRPA.cs
[unrpyc]: https://github.com/CensoredUsername/unrpyc/tree/3ae8334ed71a05535927dcc559663d3aca51215b
[engine]: https://github.com/renpy/renpy/tree/f5c62227489ba60939432f0a33dd7eceb6d83b54
[loader]: https://github.com/renpy/renpy/blob/f5c62227489ba60939432f0a33dd7eceb6d83b54/renpy/loader.py
[lexer]: https://github.com/renpy/renpy/blob/f5c62227489ba60939432f0a33dd7eceb6d83b54/renpy/lexer.py
[script]: https://github.com/renpy/renpy/blob/f5c62227489ba60939432f0a33dd7eceb6d83b54/renpy/script.py
[language]: https://www.renpy.org/doc/html/language_basics.html

## 台词解析与原生位置的验收

静态转录可同时读取 Character 的姓名表达式与本地化表，通过实际键关联姓名；保留源文件和行号。动态姓名、复杂Python、screens和表达式不可通过执行未知项目初始化来补齐。档案成员与散文件分别记录；反编译成功和静态消息导出不证明所有分支、补丁优先级或存档恢复。

## 静态分支与语法范围

从反编译 RPY 建图时，保留 if/elif/else、menu/choice、while、标签及调用的语法层级与源行。跳转、调用继续位置和返回栈分别表示，缺失、多解或动态目标保留未解决。Python/ATL 的多行表达式和不透明代码不能按普通对白扫描。不同 decompiler 可能输出无缩进的标签后续语句；应验证实际语法形式，而非把固定缩进当作全版本规则。完整性仍按[分支与存档定位](../guides/control-flow.md)验收。

<!-- EXPERIENCE:c67b01afabb3b376afb6cc7de5a7fa00b31cfebb9b6474030cc2986392669e3d:START -->
## 已验证静态RPY消息与本地化姓名键关联；不执行项目Python

- 引擎版本：RPYC decompiled RPY subset
- 方言/条件：Windows offline; explicit format checks; no runtime save loading
- 阶段：extract
- 验证等级：real_sample
- 经验 ID：`c67b01afabb3b376afb6cc7de5a7fa00b31cfebb9b6474030cc2986392669e3d`

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
<!-- EXPERIENCE:c67b01afabb3b376afb6cc7de5a7fa00b31cfebb9b6474030cc2986392669e3d:END -->

<!-- EXPERIENCE:4dac4123fd4a1b1b9d7a924ef4bf2c271b26611373c509d29843a454a2fc3e40:START -->
## 静态脚本菜单、条件体和调用目标已导出；动态表达式和返回栈未执行

- 引擎版本：unrpyc 2.0.3 decompiled syntax subset
- 方言/条件：Windows offline source/bytecode refinement; scope limited to passed files
- 阶段：extract
- 验证等级：real_sample
- 经验 ID：`4dac4123fd4a1b1b9d7a924ef4bf2c271b26611373c509d29843a454a2fc3e40`

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
<!-- EXPERIENCE:4dac4123fd4a1b1b9d7a924ef4bf2c271b26611373c509d29843a454a2fc3e40:END -->

<!-- EXPERIENCE:015b7166baa69a5069dde694d1a8aa7da888183ba7d07b18f08801a96ccfd653:START -->
## 旧存档活动上下文的原生节点身份与 RPYC 唯一匹配；回滚历史和上一条显示文本分别保留

- 引擎版本：legacy ZIP protocol-2 RollbackLog and zlib RPYC
- 方言/条件：Windows offline; only matched layouts and passed files
- 阶段：extract
- 验证等级：real_sample
- 经验 ID：`015b7166baa69a5069dde694d1a8aa7da888183ba7d07b18f08801a96ccfd653`

本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。

### 适用前提

- 使用同版本读取实现核对文件身份、区段和原生坐标
- 不同语言、归档、补丁和回滚历史保持独立来源，不推断加载优先级

### 已验证步骤

- 使用保留源码与固定版本的只读解析器导出独立结果；格式或编码不匹配即另列失败
- 核对真实样本哈希、来源坐标、记录数量与消费者或索引证据，验证范围和失败项分别报告

### 限制与失效条件

- 只证实对应阶段与匹配布局；没有全路线剧情或游戏内恢复成功声明
- 动态条件、未知消费者、补丁优先级与调用返回仍有缺口，不能将静态引用或系统指针当成完整剧情
- 原游戏内容、用户路径、标题专用参数与原始证据仅保存在本地

原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。
<!-- EXPERIENCE:015b7166baa69a5069dde694d1a8aa7da888183ba7d07b18f08801a96ccfd653:END -->
