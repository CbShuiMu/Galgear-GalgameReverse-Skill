# Majiro：ARC 与 MJO

## 解包与封包工具

| 工具与来源 | 解包或读取用途 | 封包或回写用途 | 适用版本与限制 |
| --- | --- | --- | --- |
| [GARbro CLI](../commands/garbro.md)，随附，格式标签 `MAJIRO` | 列表、解包 `MajiroArcV1.000`、`V2.000`、`V3.000` 分支 | 创建 `MajiroArcV1.000` | 当前写入器硬编码 V1，没有选择 V2/V3 的选项；只保存基本文件名，不支持子目录。能读取 V2/V3 不表示能按原版重建；见[实现][arc] |
| [Majiro V3 CLI](../commands/majiro-cli.md)，随附，MIT | 校验并提取规范 V3 平面归档，核对名称、CRC-64 哈希及索引边界 | 创建有效哈希并严格排序的 V3 归档，原样保存成员 | Python 3.9+；仅小写且可逐字节往返的 CP932 基本文件名，不支持子目录、哈希碰撞或 V2。拒绝不满足条件的名称，不自动改名；见[命令与来源](../commands/majiro-cli.md) |
| [MajiroTools][tools]，外部，未随附 | MJO 反汇编，输出 `.mjil` 及可选 `.mjres` 文本资源 | 将对应中间格式重新汇编为 MJO | 不是 ARC 封包工具；脚本操作码、字符串边界和重定位需要匹配。不能将反汇编成功当成全部控制流或语音关系已确认 |
| [GARbro CLI](../commands/garbro.md)，随附，图像读取分支 | 识别、解码所支持的 RCT/RC8 图像 | 本页不将通用图像导出流程视为所有 Majiro 图像版本的回写器 | 图像与 ARC、MJO 分开核对；保留原成员、透明度配套文件与解码元数据 |

## 格式特征与编码方式

| 格式或层级 | 通用特征 | 编码方式与判定依据 |
| --- | --- | --- |
| Majiro ARC | `MajiroArcV1.000\0` 至 `MajiroArcV3.000\0`；有条目表、名称区和内容区 | 所引 GARbro 用 CP932 读取及写入名称。V1、V2、V3 的索引项大小与哈希宽度不同，V1 通过下一位置计算大小；不能只改版本字符转为另一格式；见[实现][arc] |
| V3 名称索引 | 64 位名称哈希、32 位偏移和大小；哈希按无符号值排序，名称及正文须跟随同一顺序 | 随附 CLI 使用[原始 `hash64`][crypt]，其 CRC-64 变体不能换成标准 CRC64-ECMA。构建函数按名称小写后计算；CLI 只接受本身已小写的 CP932 名称，这一支持子集不代表所有 Majiro 分支的大小写规则 |
| ARC 内容 | 当前 GARbro 归档实现直接读取成员，没有统一成员解压或解密步骤 | 名称哈希是索引定位数据，不是正文加密；成员内部仍可有自己的压缩/加密，不能由归档层推出媒体或脚本为明文 |
| MJO 编译脚本 | 所引[反汇编器][disassembler]识别 `MajiroObjV1.000\0` 和 `MajiroObjX1.000\0`，再读取入口、函数索引和字节码长度 | X 分支对字节码执行 CRC 表驱动的 XOR 还原，V 分支不做此步骤；这是字节处理，与字符串字符编码分开。对应字符串操作数带长度及 NUL 终止符，所引实现按 Shift-JIS 解码 |
| MJIL / MJRES | `.mjil` 是工具反汇编的中间语言，`.mjres` 为外置字符串 CSV | 属于工作产物，不是引擎原生归档或源码；其中的文本编码按工具输出规则确认，不能据此判断原 MJO 编码 |
| RCT / RC8 图像 | RCT 存 RGB 图像；RC8 可作索引色图或配套透明度数据；所引[工具说明][tools]描述配套关系 | 像素、压缩、透明度和图像版本按对应读取器确认；保留可能的同名配套文件，单张 PNG 导出不证明图层与透明度完整 |
| 音频、视频及其他成员 | 按实际文件头、资源清单及脚本调用识别 | ARC 不规定统一媒体编码；标准 Ogg、WAV 或视频容器也须独立检查，不以包名代替编码证据 |

## 注意事项

先按 ARC 签名和索引项大小确认版本；核对名称解码、名称区边界、成员位置及条目数。使用 V1 写入器重建原 V2/V3 归档属于格式降级，必须单独证明目标加载器接受，不能标记为原样往返。V3 可使用随附 CLI 的已验证子集；V2 封包及子集之外的 V3 仍有缺口，不能写零哈希或改名绕过检查。

归档和脚本使用不同哈希与变换层级。MJO 中的函数名或系统调用常以哈希表示；哈希恢复结果只可作为候选，需要用参数、调用点和当前版本语义核实。修改字符串后还要由匹配的汇编器处理长度、代码位置及跳转关系，不直接按字节替换变长文本。

一个对白可能由多条 `text`、控制指令及换行组成；外置字符串导出还可能合并记录。需要对白记录时保留原始指令和跨度；需要对白与语音关联时追踪实际声音调用和姓名状态，不将 `.mjres` 的顺序当成音频顺序。

归档重建后重新提取到独立目录，比较名称、条目数与 SHA-256；脚本汇编后的完整指令与引用另行验证。仅导出图像或音频时不要求反汇编 MJO。补丁包及同名资源覆盖顺序须按当前安装确认，不从单个项目的加载顺序推广到所有 Majiro 游戏。

## 来源、版本与验证边界

- GARbro 固定为 `b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0`（MIT），用于 ARC 索引与创建能力边界。
- MajiroTools 固定为 `e0261df508b6c8065865bb51b4059263cef84394`（MIT），用于 MJO 与中间格式说明；不是引擎官方规范，也未随附。
- Majiro V3 CLI 取 [NarciBloom 归档函数][helper]（`68b1771df55896cb738c5693e2ba861557af8ca2`）与 [majiro-py 哈希库][crypt]（`f7ec450d5b78f0ed6df603b8c0b0ed79748d9cee`），均为 MIT；只保留通用归档与哈希代码，不含原项目路径、补丁逻辑或游戏内容。
- 格式与编码说明经过文档及源码核对；随附 V3 CLI 另通过合成测试，核对原始哈希库及独立位运算，并用 GARbro 独立提取、比对名称与 SHA-256。未宣称真实游戏加载验证；ARC 可读、归档可创建、MJO 可反汇编与对白语义正确是不同结论。
- 失效条件：其他 ARC/MJO 签名、未知操作码、定制加密、不同字符串约定或无法解释的图像配套关系。单款游戏参数和本地化编码留在本地，不追加为引擎通则。

[arc]: https://github.com/morkt/GARbro/blob/b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0/ArcFormats/Majiro/ArcMajiro.cs
[tools]: https://github.com/AtomCrafty/MajiroTools/blob/e0261df508b6c8065865bb51b4059263cef84394/README.md
[disassembler]: https://github.com/AtomCrafty/MajiroTools/blob/e0261df508b6c8065865bb51b4059263cef84394/src/MajiroLib/Script/Disassembler.cs
[helper]: https://github.com/RepressedAlliance/NarciBloom/blob/68b1771df55896cb738c5693e2ba861557af8ca2/tools/patch_narcissu_font.py
[crypt]: https://github.com/trigger-segfault/majiro-py/blob/f7ec450d5b78f0ed6df603b8c0b0ed79748d9cee/src/mjotool/crypt.py
