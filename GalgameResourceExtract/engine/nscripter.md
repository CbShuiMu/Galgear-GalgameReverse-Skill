# NScripter：SAR / NSA / NS2 与脚本

本页按归档布局识别，不把扩展名或 ONScripter 兼容性当作所有 NScripter 版本的证明。ONScripter 的分支与编码另见 [ONScripter](onscripter.md)。

## 解包与封包工具

| 工具与来源 | 解包或读取用途 | 封包或重建用途 | 适用范围与限制 |
| --- | --- | --- | --- |
| [GARbro CLI](../commands/garbro.md)，随附；[SAR][sar] / [NSA][nsa] / [NS2][ns2] 源码 | 读取支持的 SAR、NSA、NS2，NSA 可解开 SPB / LZSS / NBZ 成员 | 创建 SAR、NSA；NSA 可原样存储或对 BMP 使用 LZSS | NS2 在此写入器中 `CanWrite=false`；NSA 不写 SPB / NBZ 或密码保护。不能用改扩展名代替 NS2 封包 |
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
