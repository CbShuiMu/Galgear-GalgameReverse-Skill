# GalArc CLI 子集：NS2 与原样 NOA

入口为相对于本技能目录的 `tools/galarc-cli/galarc.exe`，Windows `.NET Framework 4.8` 或更高版本。运行无需 Python、.NET SDK、额外 DLL 或 GUI。两个技能分别保留完整运行文件、授权和对应构建源码，不依赖兄弟技能。

## 命令与范围

```text
galarc.exe --help
galarc.exe --version
galarc.exe list ns2 INPUT.ns2
galarc.exe extract ns2 INPUT.ns2 OUTPUT_DIR
galarc.exe pack ns2 INPUT_DIR OUTPUT.ns2
galarc.exe list noa INPUT.noa
galarc.exe extract noa INPUT.noa OUTPUT_DIR
galarc.exe pack noa INPUT_DIR OUTPUT.noa --raw
```

| 格式 | 解包能力 | 封包能力与限制 |
| --- | --- | --- |
| NS2 | 未加密、未压缩的引号名称索引，按存储顺序读取成员；严格检查索引终止符、成员大小和数据末尾 | 递归封包普通文件，保留相对路径，名称使用严格 CP932。不支持加密 NS2 或其他 NScripter 归档；SAR/NSA 另用 GARbro |
| NOA | 仅接受随附实现的规范 `Entis` / `ERISA-Archive file` 头、平面 `DirEntry`、零属性及零编码类型的 `filedata` 成员 | 仅创建新的 Raw 平面 NOA，必须显式带 `--raw`；拒绝子目录。时间戳、额外元数据及属性不保留，不提供原档元数据往返；不支持压缩、加密或未知目录结构 |

NOA 原始归档需要压缩、加密或其他存储结构时，这个 CLI 不能完成相同格式的重建。`--raw` 只是显式选择创建 Raw NOA，不证明目标引擎接受它；不能作为遇到未知格式时的自动降级方案。GARbro 的解包分支可能覆盖更多 NOA 结构，但不能由此推导此写入器支持这些结构。

## 路径、名称与输出

- `list` 的 stdout 为 JSON 数组：`name` 是归档相对名称，`offset` 是成员正文在归档内的绝对字节位置，`size` 是字节数。NS2/NOA 本 CLI 均不解码内部图像、音频或脚本。
- `extract` 和 `pack` 成功时 stdout 输出最终绝对产物路径；信息与错误以退出码和实际输出为准。参数必须通过独立 argv 传入，含空格路径在终端中用双引号括起。
- 输出文件或目录必须不存在，空目录也拒绝复用；不提供覆盖开关。先完整预检，在输出旁的临时文件/目录中处理，成功后再移动到目标；失败会清理该临时产物。
- 拒绝绝对条目名、路径穿越、Windows 设备名、非法字符、末尾空格或点、重名和文件/目录冲突。输入、输出及其现存父目录不允许符号链接或其他重解析点。
- CP932 使用严格编码/解码，并检查读取的名称字节重新编码后完全相同；非规范别名及无法往返的名称直接失败，不以 `?` 或替换字符继续。归档最大 `2 GiB - 1` 字节，创建时还为索引预留保守余量；不支持更大的成员。最终 Windows 绝对路径最多 259 个字符，临时路径也受系统限制；路径过长应选择较短工作目录。
- 输入与输出路径在检查原始路径各组成部分中的重解析点后，再归一化 `.` / `..`；被 `..` 抵消的链接目录仍拒绝。归一化后检查输出不能落入输入目录；`C:relative` 这类依赖驱动器当前目录的相对写法不支持。
- `pack` 输出必须位于输入目录外。NOA 下出现任何子目录都会失败，避免静默漏掉嵌套资源；NS2 不保存空目录。

退出码：`0` 成功（含帮助/版本），`2` 参数错误，`1` 输入、结构、编码、路径、运行或创建失败。批处理必须检查非零退出码，不能只检查是否输出日志。

## 验证与来源

创建后重新列表，并提取到另一不存在的目录，逐条比较完整相对路径、数量和 SHA-256。再用独立读取器确认产物可读；当前合成测试覆盖 NS2 递归路径、日文 CP932 名称、零字节文件，以及 Raw NOA，且用随附 GARbro 独立提取比对。拒绝覆盖、非法条目名、压缩/加密标志和链接等失败路径另有测试。没有启动真实游戏，不能将合成往返写成游戏加载验证。

上游固定为 [lunaswd/GalArc `ee1f7cda6123821fe7e5dbe456322a7cd49e95b5`](https://github.com/lunaswd/GalArc/tree/ee1f7cda6123821fe7e5dbe456322a7cd49e95b5)，GNU GPL v3 或更高版本；此子集版本为 `1.0`。只取实际使用的 NS2、NOA 与 Utility 源码，保留原授权；本地入口增加无 GUI 日志适配、格式与路径预检、暂存输出及退出码。未分发原 GUI、资源图标或其他格式实现。

分发时保留整个 `tools/galarc-cli/`，包括 `LICENSE.txt`、`NOTICE.txt`、`SOURCE.json` 与 `source/`。固定来源、文件 SHA-256 与验证边界见 `SOURCE.json`。如需重建，在该目录运行 `powershell -NoProfile -File source/build.ps1`；此步骤需要系统 .NET Framework C# 编译器。原始归档、项目路径和游戏内容不进入工具目录。
