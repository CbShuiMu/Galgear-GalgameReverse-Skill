# GARbro Mod：按条目序号解包

入口为 `tools/GARbro-cli/GalArchiveExport.exe`，与 GARbro Mod 1.0.2.2 的 DLL、`GameData/` 和许可同目录。使用 Windows .NET Framework/WPF。源文件、编译脚本和固定版来源见 [archive-export-provenance.json](../tools/GARbro-cli/archive-export-provenance.json)。

```text
GalArchiveExport.exe INPUT NEW_OUTPUT_DIRECTORY
GalArchiveExport.exe INPUT NEW_OUTPUT_DIRECTORY ALF
```

当索引有同名条目或自动识别选中其他读取器时使用。第二条命令显式指定归档标签，仍由该格式读取器验证头、索引与配套文件；先用索引证据确认标签。

输出目录必须不存在。文件按零起始条目序号保存，归档成员名称仅写入 `manifest.jsonl`。清单记录归档位置、存储大小、逻辑大小、原成员名称、SHA-256、错误及对应文件。输出是读取器的逻辑流，可能已解压或解密。保留原归档与存储范围，不能用序号文件直接替代游戏路径或当作封包基线。

退出 0 表示读取器已处理完所有索引成员，1 表示有失败，2 为用法错误。复核清单与索引的名称、偏移、大小及重复次数，重新计算输出哈希；媒体签名与脚本边界另验。外部中止可能留下未登记的临时文件。

使用 `source/build-archive-export.ps1` 重建需要系统 .NET Framework C# 编译器。编译结果放在随附 Mod 运行目录；只使用同目录 Mod 的 DLL 与数据库。

## 显式选择 PAZ 方案

```text
GalArchiveExport.exe --paz-schemes
GalArchiveExport.exe INPUT.paz NEW_OUTPUT_DIRECTORY PAZ "SCHEME NAME"
```

使用当前运行库数据库中的精确方案名称。选择仅作用于这次读取。归档名仍应匹配方案的包名表；需要对照别名时，在工作区准备只读输入副本并记录来源。即使索引可读，也须逐成员核对输出数量、哈希和合理的资源签名。有关来源与版本差异见 [MUSICA PAZ](../engine/musica.md)。
