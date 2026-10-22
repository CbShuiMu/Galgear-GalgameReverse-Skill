# Siglus CLI：场景归档与上游命令

随附入口为 `tools/siglus-ssu/siglus-ssu.exe`，路径相对于本技能根目录；Windows x64，自包含运行时。固定上游 SSSU `0.5.7`，Unlicense / 0BSD 双许可证；本仓库增加保留包级元数据的归档适配。源码、授权、固定提交、下载哈希和重建脚本见同目录的 `NOTICE.txt`、`VERSION.json`、`LICENSE`、`PYTHON-LICENSE.txt`、`licenses/` 与 `source/`。这些工具不依赖另一个技能或仓库根目录。

## 归档适配命令

| 命令 | 用途与限制 |
| --- | --- |
| `siglus-ssu.exe --help` | 显示归档适配帮助 |
| `siglus-ssu.exe --version` | 显示固定上游版本 |
| `siglus-ssu.exe unpack <Scene.pck> <new-directory> [--angou <source>]` | 提取全部已解码场景 DAT 到新目录；输出目录必须不存在。原始 PCK 继续作为完整基线，嵌入源码留在原包 |
| `siglus-ssu.exe pack <dat-directory> <new.pck> --base <original.pck> [--angou <source>]` | 保留原场景身份及包级元数据，只替换现有 DAT。输入目录只含全部匹配的普通 DAT 文件，输出文件必须不存在 |

`pack --base` 校验已知 92 字节头、名称与条目计数、索引边界和连续数据布局。没有改动的成员保留原压缩或变换字节；有改动的成员沿用已识别的原样、LZSS 或公共 XOR + LZSS 层，再应用原包声明的项目 XOR。没有改动时可做到整个 PCK 字节一致。若原包包含嵌入源码，修改 DAT 默认报错，避免旧源码与新脚本不符；未知布局、缺失或新增场景也报错，不静默简化归档。

归档适配会在路径归一化前后逐级拒绝符号链接、junction 及其他 reparse point，包括可能被 `..` 消去的父级链接；输入归档、基线、DAT 根目录、成员和输出路径都受此约束。输出必须在 DAT 根目录之外，不能覆盖已有文件、目录或悬空链接。提取与封包先写同一父目录中的临时产物，再通过 Windows 原子重命名发布；写入失败不会发布半成品，临时产物及本次创建的空父目录会清理。

`--angou` 使用上游的显式密钥来源规则，按当前项目的实际授权输入提供路径或本地参数，详情见[固定版上游手册][manual]。工具可能在本地诊断中打印密钥信息；不要将该输出、项目路径或游戏密钥收录到技能包。没有正确密钥时不能宣称完成解包。

```powershell
$tool = '.\tools\siglus-ssu\siglus-ssu.exe'
& $tool unpack .\original\Scene.pck .\work\scene-dat

# 编辑场景 DAT 后，使用原包基线封包到新文件
& $tool pack .\work\scene-dat .\rebuilt\Scene.pck --base .\original\Scene.pck

# 重新解包，核对每个场景名称、数量与 DAT 哈希
& $tool unpack .\rebuilt\Scene.pck .\verify\scene-dat
```

这些 DAT 已经过内部解压或解密，工作目录不等于原样 PCK 的字节基线。原归档、工作 DAT、修改输入和验证目录分别存放；包级属性/命令表变化或新增场景不在适配入口的范围内。

## 保留的上游命令

以 `-x`、`-c` 等上游模式开头的参数原样交给 SSSU。上游命令与归档适配的输出和覆盖规则不同，按[固定版手册][manual]执行。

| 上游模式 | 用途与边界 |
| --- | --- |
| `-x <Scene.pck> <output-parent>` | 解包到自动创建的时间戳目录，尝试恢复嵌入原源码；实际目录打印在 `Output:` 后 |
| `-x --disam <Scene.pck> <output-parent>` | 在解包结果之外生成场景反汇编工作文件 |
| `-x --decompile <Scene.pck> <output-parent>` | 实验性反编译，不保证得到可可靠往返的源码 |
| `-c <source-directory> <new.pck>` | 从完整且版本匹配的 `.ss` / `.inc` 源码编译；不应以实验反编译结果替代真实源码 |
| `-c --dat-repack [--no-os] [--no-lzss] <dat-directory> <new.pck>` | 从 DAT 新建包；缺少 `.inc` 时不能恢复原包的 include 元数据。完整重建优先使用上面的 `pack --base` 并核对其适用范围 |

需要完整上游帮助时运行 `siglus-ssu.exe -x --help`。上游还提供媒体及文本等操作；本构建没有可选 Pillow、psutil 和 Rust 扩展，不宣称所有这些模式均可用。工具中提供的游戏启动与引擎补丁模式不在常规资源处理流程内，执行前仍须具有对应用户授权。

## 输出与验证

归档适配成功返回 `0` 并向 stdout 输出 JSON 摘要；处理失败返回 `1`，参数错误由 argparse 返回 `2`，诊断写入 stderr。`pack` 在内存中重新检查输出的场景身份与 DAT 内容后才创建目标；仍应使用独立提取流程做交付核验。

本仓库的 `tests/test_siglus_cli.py` 只使用临时合成资源，检查独立单 EXE 运行、帮助/版本、压缩与原样成员往返、合成项目 XOR、非空 include 表保留、不同成员长度、嵌入源码保护、真实父级链接及 `..`、已有/悬空输出拒绝和实际提取 IO 失败后的原子发布边界。不启动真实游戏，不将这些检查称作游戏兼容验证。

## 来源与重建

上游固定提交为 `85700715aed8695a95183bb973f981a61ae9d9c7`；官方 PyPI 的 `siglus_ssu-0.5.7-py3-none-any.whl` SHA-256 为 `c4f45ac11f1650c00d284a477bda23c6c9be58b0eb3db32d3f7c544da72c8509`。随附 40 个上游 Python 文件均与该提交逐文件一致，没有修改；本仓库的 `archive_cli.py`、`entry.py`、`build.py` 使用 0BSD。上游原本就是 CLI，无 GUI；不随附开发缓存、Rust 构建目录或游戏数据。

自包含程序使用官方 CPython `3.12.10` Windows x64 embeddable distribution、PyInstaller `6.21.0` 和 pyinstaller-hooks-contrib `2026.9` 构建。运行时下载 URL、原包哈希和成品哈希见 `VERSION.json`。Python、PyInstaller、hooks 及运行时所用 OpenSSL、libffi、bzip2、XZ 的授权文本都随工具保留。

在干净的官方 Windows Python 3.12 环境安装构建依赖后，于工具目录运行：

```powershell
python -m pip install PyInstaller==6.21.0 pyinstaller-hooks-contrib==2026.9
python .\build.py --output C:\Temp\siglus-cli-build
```

成品位于指定目录的 `dist/siglus-ssu.exe`。构建脚本包含全部动态 CLI 模块、发行元数据及 `const.py` 原文件；后者由上游运行时读取来计算常量哈希，不能删除。源码入口为 `python entry.py --help`，需要 Python 3.12+；归档适配的原子发布实现要求 Windows，运行时不下载依赖。

[manual]: https://github.com/Jirehlov/SiglusSceneScriptUtility/blob/85700715aed8695a95183bb973f981a61ae9d9c7/manual.md
