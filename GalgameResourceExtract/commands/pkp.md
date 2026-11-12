# PKP v0 只读 CLI

使用本技能随附的 `tools/pkp-cli/pkp.py`。需要 Python 3.10+ 标准库。源码独立实现，许可见 [LICENSE](../tools/pkp-cli/LICENSE)。

```powershell
python tools/pkp-cli/pkp.py list INPUT
python tools/pkp-cli/pkp.py extract INPUT NEW_OUTPUT_DIRECTORY
python tools/pkp-cli/pkp.py extract INPUT NEW_STORED_DIRECTORY --stored
```

按字节识别 `PKP\0`，版本字段为 0。当前实现接受 12 字节头和 176 字节定长索引，记录含小端偏移、逻辑长度、存储长度、零保留字段和 NUL 结尾的 UTF-16LE 名称。存储范围从索引后连续至文件末尾，逻辑流为裸 DEFLATE。以上条件来自实际补丁样本。相同扩展名的其他文件须重新识别。

`list` 输出 JSON 索引。解包要求输出目录尚不存在，成员按序号写出，原名称与偏移保留于 `manifest.jsonl`。逐条核对解压结束、消费范围、逻辑长度及输出 SHA-256。需要存储层时使用 `--stored`，用单独目录和同一索引保留压缩字节。输入保留原件。

退出 0 表示命令成功，退出 1 表示格式、I/O 或成员读取失败，退出 2 表示用法错误。有失败时清单保留对应的条目和错误。原样逻辑成员可能仍为 PS2A、PB3 等引擎内部格式，后续脚本、图像或覆盖语义另验。
