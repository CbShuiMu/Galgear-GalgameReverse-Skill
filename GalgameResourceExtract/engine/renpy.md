# Ren'Py：RPA 归档与 RPY / RPYC 脚本

RPA 是资源容器，RPYC 是编译脚本；解包、脚本反编译、重新编译和资源封包分别验证。

## 解包与封包工具

| 工具与来源 | 解包或读取用途 | 封包或重建用途 | 适用范围与限制 |
| --- | --- | --- | --- |
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
