# ONScripter：兼容归档与脚本编码

ONScripter 是 NScripter 兼容实现，多个分支的文字、命令和资源支持存在差异。本页限定到所引 Ogapee 主线实现，不把 ONScripter-EN、RU 或其他汉化分支的行为混写为统一规则。

## 解包与封包工具

| 工具与来源 | 解包或读取用途 | 封包或重建用途 | 适用范围与限制 |
| --- | --- | --- | --- |
| [GARbro CLI](../commands/garbro.md)，随附 | 解包其支持的 SAR / NSA / NS2 | 创建 SAR / NSA | NSA 创建只提供原样存储、BMP 的 LZSS，不写 SPB / NBZ；NS2 没有此后端写入能力，结构见 [NScripter](nscripter.md) |
| [GalArc CLI](../commands/galarc.md)，随附适配工具 | 按命令页读取标准 NS2 | 补齐命令页列明的标准 NS2 创建 | 不包含整套 ONScripter 运行时，不证明目标分支加载兼容 |
| [Ogapee ONScripter][upstream]，外部 GPL-2.0-or-later 源码参考 | `nsadec.cpp`、`sardec.cpp` 和 `nscriptdecode.cpp` 提供归档与脚本包装的实现依据 | 读取器含部分归档写入辅助；不是已随附的通用封包 CLI | 引擎源码不是本技能运行依赖，也不应通过启动游戏替代归档验证 |
| [ONScripter-Tools][tools]，外部 GPL 工具 | `nscdec`、`nsadec`、`ns2dec`、`sardec` | `nscmake`、`nsamake`、`ns2make`、`sarmake` | 未随附；其旧版 `-ns2` / `-ns3` 偏移参数与 NS2 格式名不同，具体参数按所用版本说明 |

## 格式特征与编码方式

| 层级 | 通用识别特征 | 编码或变换方式与判定依据 |
| --- | --- | --- |
| 归档与文件名 | 可用 `arc.sar`、`arc.nsa`、编号 `.ns2` 或散文件；以实际命令和归档布局确认 | 结构与字段字节序见 [NScripter](nscripter.md)。所引读取器按字节匹配并规范化 ASCII 大小写，不能把路径按系统区域设置任意转码 |
| 默认脚本文字 | 主线 [Encoding.cpp][encoding]默认 `CODE_CP932` | 按 CP932 解码，不用“ANSI”指代不明确编码，也不把某款作品的 GBK 等汉化编码推广到所有 ONScripter |
| 主线 UTF-8 路线 | 所引 [ScriptHandler.cpp][script]识别 `pscript.dat` 后将文字读取切到 `CODE_UTF8` | 在这一路线先处理脚本包装，再按 UTF-8 读取。不是给任意 `0.txt` 加 BOM 即可切换；分支改动必须核对它自己的实现 |
| 脚本包装 | 主线优先查找明文 `0.txt` / `00.txt`，也支持多种 DAT / 安全脚本形式 | 标准 `nscript.dat` / `pscript.dat` 路线逐字节 XOR `0x84`；其他包装另有模式和密钥表。变换与 CP932 / UTF-8 的文字解码分开 |
| 压缩与媒体 | NSA 可含 SPB、LZSS、NBZ；部分扩展还可由读取器注册 | SPB、LZSS、bzip2 / NBZ 是成员压缩；WAV、Ogg、MP3 等是媒体格式。按成员文件头、插件注册及分支能力核对，不据脚本文字编码判断媒体 |

## 注意事项

- 先记录具体分支、提交或版本；命令兼容不能证明文字、字体、存档和媒体加载全部兼容。所引主线默认 CP932 的结论不自动覆盖 ONScripter-EN 等分支。
- 读取器会按实际脚本决定归档使用方式；编号脚本、散文件与归档应保留各自来源、完整路径和加载线索。输出原样资源根目录之外的工作副本再做文本转换。
- 只需资源解包时不强制解释脚本。需要对白与语音关联时按具体分支的实际播放命令和路径引用建立证据，不能根据归档顺序或声音文件序号猜配。
- 创建后独立解包比对条目，再验证文字解码和脚本包装。未运行目标引擎时如实标记加载兼容未验证。

## 来源、版本与验证边界

主线实现固定为 Ogapee ONScripter `848a60892e4d721459e8d1051e1b8fe45164c3e9`，归档工具依据 GARbro `b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0`；外部工具说明固定为 `c28bb8b383addac76413027d0bd9360a0834d973`。本页是实现参考，未做真实游戏或运行验证；其他分支、代码页、归档偏移和插件行为不同即缩小适用范围，项目专用参数不收录为通则。

[upstream]: https://github.com/ogapee/onscripter/tree/848a60892e4d721459e8d1051e1b8fe45164c3e9
[encoding]: https://github.com/ogapee/onscripter/blob/848a60892e4d721459e8d1051e1b8fe45164c3e9/Encoding.cpp
[script]: https://github.com/ogapee/onscripter/blob/848a60892e4d721459e8d1051e1b8fe45164c3e9/ScriptHandler.cpp
[tools]: https://github.com/GoldbarGames/ONScripter-EN-Steam/blob/c28bb8b383addac76413027d0bd9360a0834d973/tools/readme.txt
