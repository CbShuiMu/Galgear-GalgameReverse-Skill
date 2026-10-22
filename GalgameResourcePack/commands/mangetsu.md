# Mangetsu CLI 调用约定

用于 Tsukihime Remake Switch 数据格式：MRG/HED/NAM、MZP、MZX、NXX、HFA，以及特定脚本文本表。程序均位于相对于本技能目录的 `tools/mangetsu/`；Windows x64 原生 CLI，无 WSL、CMake、编译器或 GUI 运行依赖。

使用绝对路径调用程序，将每个参数作为独立 argv 传递。以下 `BASE` 是不含 `.mrg/.hed/.nam` 后缀的共同路径；`.mrg` 与 `.hed` 必须成对，`.nam` 可选。

```text
mrg_info.exe [--csv] BASE
mrg_extract.exe [-i INDEX ...] BASE [OUTPUT_DIR]
mrg_pack.exe OUTPUT_BASE [--names NAME_LIST] FILE1 [FILE2 ...]
mrg_replace.exe -iINDEX1 FILE1 [-iINDEX2 FILE2 ...] INPUT_BASE OUTPUT_BASE
nam_read.exe INPUT.nam
mzp_info.exe INPUT.mzp
mzp_compress.exe OUTPUT.mzp FILE1 [FILE2 ...]
mzp_extract.exe INPUT.mzp [OUTPUT_DIR]
mzx_compress.exe INPUT OUTPUT
mzx_decompress.exe INPUT OUTPUT
nxgx_compress.exe INPUT OUTPUT
nxx_decompress.exe INPUT OUTPUT
hfa_extract.exe INPUT.hfa [OUTPUT_DIR]
script_text_to_content_json.exe SCRIPT_TEXT.mrg OUTPUT.json
repack_script_text_translation.exe TRANSLATIONS.json SCRIPT_IN.mrg SCRIPT_OUT.mrg
```

- `mrg_info --csv` 输出无表头 CSV：索引、扇区偏移、压缩后扇区数、解压后扇区数、名称。名称可能包含 CSV 特殊字符；需要可靠清单时结合 `.nam` 和索引核对。
- `mrg_extract -i INDEX` 可重复；索引从 0 开始。注意其语法与 `mrg_replace -iINDEX` 不同。输出名附有索引及可选 NAM 名称；不是原始名字的直接还原。
- `mrg_pack` 按 argv 文件顺序排列条目，不接受目录或由工具展开的通配符。`NAME_LIST` 每行一个名称，与输入文件逐一对应。重建保持原索引顺序。
- MRG 使用 0x800 字节扇区，提取内容可能包含尾部填充。不要自动 trim 零字节；可用记录的大小与格式解码结果验证。单条目的扇区计数为 16 位，封包前检查不超过 65535 个扇区。
- `mrg_replace` 只写 `.mrg/.hed`，不复制 `.nam`；保持原 NAM 时自行复制到新的 BASE。预先验证替换索引在原条目范围内。输入、输出 BASE 必须不同。
- MZP 保留输入顺序；`mzp_compress` 只封装，不执行 MZX/NXX 压缩。`mzp_extract` 输出 `输入文件名_0000.bin` 等；显式提供空输出目录。
- `mzx_compress` 仅生成有效的 literal 流，通常比输入大；不保证压缩率。NXX 的 NXGX 使用 zlib；NXCX 没有真实样本验证。
- `hfa_extract` 只提取；无对应 HFA 封包器。
- 两个脚本文本工具处理的 `.mrg` 实际为特定 MZP 字符串表，不是任意 MRG。JSON 为 `script_text_by_hash[hash] = {jp, en, notes}`，其中 `hash` 是 SHA-256 的大写十六进制表示；回填读取非空 `en`，不自动翻译，也不生成对白映射。
- 没有统一 `--help`；无参数输出用法并返回非零。成功返回 0；错误非零，严重格式错误可能直接终止。部分日志写 stderr，不能仅凭 stderr 判断失败。
- 工具可能覆盖输出；始终选择新的文件/空目录，预先创建输出文件父目录。原始文件保持独立；重建后重新提取并核对索引、名称、有效载荷与填充。

分发保留所有 `.exe` 和 `licenses/`。此包使用静态 CRT/zlib 和 Windows 系统 SHA-256，不需要额外 DLL。Windows 文件路径宜使用 ASCII 工作目录；尚未验证全部工具对非 ASCII 路径的兼容性。
