# 来源与抽象

阅读日期：2026-10-22。以下是用户指定的 11 篇文章。这里提炼决策方法，不分发原文、示例游戏文件或整套代码；地址、格式和平台经验均需在目标版本重新验证。

## 文章到方法的映射

| 编号 | 原文 | 提炼的方法 | 在本技能中的位置 |
| --- | --- | --- | --- |
| R1 | YuriSizuku：[文本加密（压缩）解密](https://blog.schnee.moe/posts/GalgameReverse1/) | 从已知文本回溯生产者，以实际输入输出恢复算法；先行为等价，再整理实现 | [资源与算法](../guides/formats-and-algorithms.md) |
| R2 | YuriSizuku：[系统字库与文字编码](https://blog.schnee.moe/posts/GalgameReverse2/) | 将路径转换、文本解释、字符遍历和字体选择分开定位 | [编码与字体](../guides/text-and-fonts.md) |
| R3 | YuriSizuku：[自定义字库分析](https://blog.schnee.moe/posts/GalgameReverse3/) | 用索引到像素坐标的观测解释复杂布局，同时恢复码表和图集 | [编码与字体](../guides/text-and-fonts.md) |
| R4 | YuriSizuku：[IDA 静态分析 PSV 游戏](https://blog.schnee.moe/posts/GalgameReverse4/) | 结合索引、magic 和分发逻辑定位实现；谨慎迁移伪代码中的位宽、指针与常量表 | [资源与算法](../guides/formats-and-algorithms.md) |
| R5 | YuriSizuku：[Switch 平台下的 Unity 后端 IL2CPP 分析](https://blog.schnee.moe/posts/GalgameReverse5/) | 配对原生模块与 metadata，沿语言状态的初始化、写入及读取追踪实际消费者 | [原生程序与 IL2CPP](../guides/native-and-il2cpp.md) |
| R6 | YuriSizuku：[动态汉化分析：MAJIROv3](https://blog.schnee.moe/posts/GalgameReverse6/) | 以脚本身份和相对偏移关联运行时文本，检查显示、历史记录和重复加载是否一致 | [运行时替换](../guides/runtime-replacement.md) |
| R7 | YuriSizuku：[动态汉化分析 2：AZsystem](https://blog.schnee.moe/posts/GalgameReverse7/) | 将替换提前到完整资源层，统一处理容量、脚本引用及图像通道布局 | [运行时替换](../guides/runtime-replacement.md) |
| R8 | YuriSizuku：[哈希算法分析：krkrz_hxv4](https://blog.schnee.moe/posts/GalgameReverse8/) | 从资源解析链分离名称映射与内容变换，用运行时样本检验离线哈希实现 | [资源与算法](../guides/formats-and-algorithms.md) |
| RS1 | YuriSizuku：[ARM/ARM64 ELF 中汉化字符串超长修改方法](https://blog.schnee.moe/posts/GalgameReverse_special1/) | 在可加载区域放置长字符串，再根据实际寻址方式更新引用 | [原生程序与 IL2CPP](../guides/native-and-il2cpp.md) |
| D1 | Dir-A：[GalGame 引擎免封包略谈](https://www.cnblogs.com/Dir-A/p/18096904) | 实测目录与归档的加载优先级，核对裸文件的数据状态和分配器所有权 | [运行时替换](../guides/runtime-replacement.md) |
| D2 | Dir-A：[GalGame 封包逆向入门](https://www.cnblogs.com/Dir-A/p/17737084.html) | 结合正向架构、函数输入输出、静态结构与动态回溯逐步定位关键逻辑 | [资源与算法](../guides/formats-and-algorithms.md) |

## 抽象时保留的边界

- 压缩、加密、字符编码和脚本解释是不同层。不能沿用部分历史文章将它们合称“加密”的简写方式。
- 已知引擎的目录加载、原样模式、哈希种类和检测公式是实验线索，不是同名引擎所有版本的保证。
- 历史示例中的编码别名、汇编文字和 API 用法可能不够精确。具体实现以目标指令、SDK、文件格式及实际输入输出为依据，不逐字移植。
- 工具名称只表示可能的能力。先确认本机版本、平台和输入支持，再执行；不把文章中的旧版本组合固定为安装要求。
- 本技能增加的版本锁定、证据记录、回归范围及跨阶段交接是工程约定，不是原文已经为当前游戏完成的验证。

## 核对实现细节的第一方资料

- Microsoft：[代码页标识](https://learn.microsoft.com/en-us/windows/win32/intl/code-page-identifiers)、[MultiByteToWideChar](https://learn.microsoft.com/en-us/windows/win32/api/stringapiset/nf-stringapiset-multibytetowidechar)、[LOGFONTA](https://learn.microsoft.com/en-us/windows/win32/api/wingdi/ns-wingdi-logfonta)：确认编码标识、长度单位和字体参数。
- Microsoft：[Windows x64 调用约定](https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention?view=msvc-170)、[Detours 用法](https://github.com/microsoft/Detours/wiki/Using-Detours)：确认目标与替换函数的签名及 ABI。
- System V：[ELF Program Loading](https://gabi.xinuos.com/elf/07-pheader.html)：确认文件布局、加载段及映射关系；主机平台外层封装还需单独确认。
- Arm：[AAPCS64](https://github.com/ARM-software/abi-aa/blob/main/aapcs64/aapcs64.rst)：确认 AArch64 调用约定；指令编码另查目标架构的指令手册和实际反汇编。
- Unity：[IL2CPP scripting back end](https://docs.unity3d.com/Manual/scripting-backends-il2cpp.html)：确认 IL2CPP 的原生代码生成方式。分析工具输出不等于恢复了原始 C# 方法实现。
