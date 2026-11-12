# rUGP CRsa 脚本载荷 CLI

`tools/age-rio-cli/crsa_extract.py` 使用 Python 3.10+ 标准库及随附的 AgeReVerse RIO 块读取实现。先用 [RIO 目录 CLI](age-rio.md) 生成 JSON，再显式绑定各卷。

```powershell
python tools/age-rio-cli/crsa_extract.py inventory.json NEW_OUTPUT_DIRECTORY --volume base.rio --volume base.rio.002
```

卷的文件名须匹配目录中的 `volume`。脚本按目录条目序号保存为 `.crsa` 原始记录和 `.plain` 解密 VM 载荷；`manifest.jsonl` 保留逻辑路径、卷内范围、头部长度和两层 SHA-256。只读输入。输出目录须尚不存在。某条记录失败时保留错误及其余成功条目，退出码为 1。

对已识别的 11 字节或 12 字节对象头，分别核对加密长度字段、每个完整块与末尾短块的校验和，并要求实际消耗恰好覆盖目录范围。未知对象头、越界范围和超过 16 MiB 的记录会被拒绝。该 CLI 处理目录登记的脚本；目录外扫描、RUO 覆盖关系、VM 指令、对白消费者和存档语义各自验证。见 [rUGP 引擎资料](../engine/rugp.md)。

继续还原剧情时，先按 CRsa 载荷版本分流。v18 可用顺序指令读取器核对命令计数、字符串池和后置引用，再按 `CVmMsg3` 的语言索引导出对白。以有效 RUO 重定向关联基础脚本身份，保留原版与覆盖载荷各自的来源。只在同一消息字段有显式说话人标记时直接填写姓名，保留其余字段原文和未知状态。v17 应使用匹配的 `CVmMsg` 字段布局。静态调用、标签、选择和存档指令坐标可以单独导出，实际选项效果和存档恢复需用游戏行为或匹配存档验证。
