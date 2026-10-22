# Majiro CLI：ARC V3

入口为本技能内的 `python tools/majiro-cli/majiro_cli.py`。需要 Python 3.9 或更高版本，仅使用标准库，无 GUI、额外模型或游戏程序依赖。工具可独立随本技能安装；整个 `tools/majiro-cli/` 目录中的来源、许可证与 Python 源码必须一起保留。

## 命令与范围

```powershell
python tools/majiro-cli/majiro_cli.py --help
python tools/majiro-cli/majiro_cli.py --version
python tools/majiro-cli/majiro_cli.py list C:\Work\original.arc
python tools/majiro-cli/majiro_cli.py extract C:\Work\original.arc C:\Work\original-resources
python tools/majiro-cli/majiro_cli.py pack C:\Work\staging C:\Work\rebuilt.arc
```

| 项目 | 支持与限制 |
| --- | --- |
| 格式 | 仅 `MajiroArcV3.000` 的规范平面布局；不创建 V1/V2，不把原包转为其他版本。V1 仍可使用 GARbro；V2 封包仍有缺口 |
| 名称 | 只接受本身等于 Python `lower()` 结果的 CP932 基本文件名。非小写名称直接失败，不静默改名，也不生成另一组名称哈希 |
| 名称字节 | 严格 CP932 解码及重新编码须逐字节一致；无法往返的字符与非规范别名拒绝。名称最多 255 个 Unicode 字符；不支持子目录、路径分隔符、Windows 设备名或非法字符 |
| 索引 | 使用 Majiro 的非标准 CRC64；索引按无符号哈希严格递增排列，名称、偏移及正文跟随同一顺序；拒绝碰撞或名称哈希不符的输入 |
| 成员 | 原样保存正文，包括零字节成员；不解密 MJO、不编译脚本、不解码图像或音频，也不向包中添加工作元数据 |
| 大小 | 默认归档及累计提取上限 256 MiB；全局 `--max-bytes N` 可调整至不超过 `4294967295`。索引最多 16 MiB，最多 100000 个成员；不超出格式的 32 位位置与大小字段 |
| 输出 | 文件或目录必须不存在，不提供覆盖开关；输出归档必须在输入目录之外。先在同目录暂存，验证后非覆盖发布；需要支持文件硬链接的文件系统来原子发布创建结果 |

`list` 校验全部索引后输出 JSON：顶层有 `version`、`count`、`entries`，成员包含 `name`、十六进制 `name_hash`、归档绝对字节位置 `offset` 和字节数 `size`。`extract` / `pack` 成功时输出含绝对 `output` 路径的 JSON。成功返回 `0`，数据或运行错误返回 `1`，参数错误返回 `2`；错误写入 stderr。

输入、输出及原始路径组成部分中的符号链接和重解析点均拒绝，包括随后被 `..` 抵消的目录；检查后再归一化路径。解包会先检查名称、排序、哈希与范围，拒绝部分重叠、截断和未说明的名称区填充；不以“能输出文件”代替完整性检查。创建使用上游函数的内存构建方式，大小上限不是流式写入保证，输入应与可用内存相称。

## 方法与验证边界

V3 构建流程摘自 [NarciBloom 的 `archive(files)`][helper]，MIT；已移除原项目路径及集成代码，仅保留归档函数。CRC64 直接使用 [majiro-py 原始 `crypt.py`][crypt] 的 `hash64`；其算法与标准 CRC64-ECMA 不同，不能用同名标准库算法替换。所引函数对名称调用 `lower()`，本 CLI 通过拒绝不满足小写条件的输入来限定已确认范围，不推断所有 Majiro 分支的大小写规则。

验证等级为合成：测试名称、索引和正文同步排序，CRC64 与原始库及独立位运算结果一致，创建后由本 CLI 和 GARbro 分别提取并比对完整文件集合、数量及 SHA-256；还覆盖空成员、名称字节、路径、大小、版本与覆盖失败条件。未启动真实游戏，不能用这些结果宣称全部 V3 游戏兼容。

固定版本与文件哈希记录在 `tools/majiro-cli/SOURCE.json`。NarciBloom 固定为 `68b1771df55896cb738c5693e2ba861557af8ca2`；majiro-py 固定为 `f7ec450d5b78f0ed6df603b8c0b0ed79748d9cee`。`crypt.py` 保留原始内部路径及代码，仅摘录其实际需要的两个整数辅助函数并使用最小包入口。分发保留 `LICENSE.txt`、`NOTICE.txt`、`licenses/` 和 `source/`；不依赖未安装的兄弟技能。

遇到不同签名、非小写或非规范 CP932 名称、未知哈希、索引布局差异时停止套用。项目专有规则留在本地，不能为了生成归档跳过校验或写零哈希。创建后再次解包比对；目标加载与脚本语义仍应独立验证。

[helper]: https://github.com/RepressedAlliance/NarciBloom/blob/68b1771df55896cb738c5693e2ba861557af8ca2/tools/patch_narcissu_font.py
[crypt]: https://github.com/trigger-segfault/majiro-py/blob/f7ec450d5b78f0ed6df603b8c0b0ed79748d9cee/src/mjotool/crypt.py
