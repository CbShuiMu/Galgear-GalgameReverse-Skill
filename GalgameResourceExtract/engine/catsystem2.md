# CatSystem2：INT、CST 与 HG 图像

## 解包与封包工具

| 工具与来源 | 解包或读取用途 | 封包或回写用途 | 适用版本与限制 |
| --- | --- | --- | --- |
| [GARbro CLI](../commands/garbro.md)，随附，格式标签 `INT` | 列表、解包 `KIF\0` 归档；读取器识别未加密索引的两种名称字段长度，以及带 `__key__.dat` 的加密分支 | 创建未加密 `INT`，CP932 文件名，64 字节名称字段 | 只保存基本文件名，不支持子目录；写入器没有加密选项。读取加密分支需要当前归档对应的方案，不能把可读视为可按原加密方式重建；见[实现][int] |
| [CatSystem2 官方工具][official-data]，外部，未随附 | 官方文档说明场景、界面、图像等资源的分工 | `mc.exe` 将场景源码编译为 CST；`fes.exe` 编译界面脚本；`WGC.exe` 转换 HG3 | 成员编译和图像转换不等于 INT 封包；工具版本、许可证和源码是否完整须分别核对，不直接将官方 SDK 复制进技能 |
| [TriggersTools.CatSystem2][cst-source]，外部源码参考，未随附 | 读取 CST 的压缩层、记录类型、字符串和偏移表 | 本页不将其作为已验证的通用封包 CLI | 固定提交实现可用于核对旧版格式；遇到读取器不认识的记录或新版结构时停止套用 |

## 格式特征与编码方式

| 格式或层级 | 通用特征 | 编码方式与判定依据 |
| --- | --- | --- |
| INT / KIF 归档 | 文件头 `KIF\0`，随后为条目计数；索引包含名称、位置和大小 | 所引 GARbro 实现用 CP932 解码名称。未加密读取分支尝试 32 或 64 字节名称字段；创建器固定用 64 字节。名称编码不证明脚本正文编码；见[实现][int] |
| INT 加密分支 | 第一条索引名为 `__key__.dat`；名称和条目位置处理不同于普通索引 | 所引实现采用 Blowfish、伪随机数及名称变换。此处属于归档字节处理，不能用字符转码替代；实际凭据、参数和项目证据只留本地 |
| CST 场景 | `CatScene` 八字节标识及压缩前后长度；解压后有输入记录、偏移表与字符串表 | 所引[读取器][cst-source]先做 zlib 解压，再按记录类型读取 NUL 结尾字符串，并使用 Shift-JIS。仅在该结构及读取分支匹配时作为正文编码依据，不用文本自动探测取代结构检查 |
| 场景源码与 FES 界面脚本 | 官方将场景和界面脚本分开；`mc.exe` 的输入为文本，输出为 CST | 源码、编译结果与导出中间文件是不同层级。按匹配版本编译器或读取实现确认编码；不能将其他引擎同名 `.cst` 或任意 `.txt` 直接套用 |
| HG-2 / HG-3 图像 | HG3 采用 `HG-3` 标识，可包含多个帧、帧 ID 与位置数据；见[官方图像说明][official-hg3]和[格式实现][hg3-source] | 图像内部压缩和像素编码与脚本文字独立；导出 PNG 只能作为工作资源，必须保留帧 ID、偏移、原画布等元数据及原成员 |
| 音频、视频及其他成员 | 按提取后的实际文件头和脚本引用识别，不根据 `pcm` 等包名确定编码 | Ogg、WAV 等媒体必须分别检查容器、编码和必要的标签；INT 不定义统一媒体编码 |

## 注意事项

先核对 INT 条目清单、名称字段与输出数量。原始归档保留不动；GARbro 对加密 INT 输出的是解密后的成员，记录为成员层的原样资源根目录，不能声称保留了归档的加密存储字节。解码 HG 图像或解析 CST 时另建工作目录。

使用 `INT` 写入器重建前，确认目标接受未加密归档及 64 字节名称布局。先用合成文件或获授权的代表性成员创建、重新提取并比较相对名称与 SHA-256；这些检查不能证明目标加载器接受降为未加密的归档。原样往返需要加密或旧布局时，当前写入器存在能力缺口。

官方场景文本规则区分姓名与正文，并允许变量、换行和控制记号；见[文字规则][official-text]。需要对白记录时按 CST 类型和消息边界解析，先保存原始记录位置，再做文本清理。需要对白与语音关联时跟随实际声音命令和当前姓名状态，不按条目顺序或语音文件名猜测。界面脚本及姓名表可能含额外显示文本，应按用户要求纳入统计。

## 来源、版本与验证边界

- 官方手册按 2026-10-22 在线版本核对，描述资源分工与制作流程；它不是所有商业分支的二进制格式规范。
- GARbro 来源固定为 `b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0`（MIT）；CST 读取参考固定为 TriggersTools.CatSystem2 `47fdcb605c16a5d93a97cb2894684326f21885c8`。
- 本页验证等级为文档与源码核对，没有宣称真实游戏运行验证。官方资源分工、INT 与 CST 的不同层级分别核验，不能用封包成功证明脚本文字或对白语义正确。
- 失效条件：签名、索引宽度、加密分支、CST 结构或图像版本不符；未知方案、定制加载器及单款游戏补丁参数先留本地，不作为引擎通则收录。

[int]: https://github.com/morkt/GARbro/blob/b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0/ArcFormats/CatSystem/ArcINT.cs
[official-data]: https://cs2.suki.jp/manual/data/index.html
[official-text]: https://cs2.suki.jp/manual/data/text/text.html
[official-hg3]: https://cs2.suki.jp/manual/data/image/img_file.html
[cst-source]: https://github.com/trigger-segfault/TriggersTools.CatSystem2/blob/47fdcb605c16a5d93a97cb2894684326f21885c8/src/TriggersTools.CatSystem2.Shared/Extract/CstScene.Extract.cs
[hg3-source]: https://github.com/morkt/GARbro/blob/b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0/ArcFormats/CatSystem/ImageHG3.cs
