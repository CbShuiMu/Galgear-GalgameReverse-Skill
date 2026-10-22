# Ethornell CLI 调用约定

用于技能的 BGI/Ethornell `BURIKO ARC20` 归档和 `DSC FORMAT 1.00` 压缩流处理。入口为相对于本技能目录的 `tools/ethornell/ethornell.exe`；Windows x64，无 Python、GUI 或安装步骤。使用绝对路径调用，参数以独立 argv 传递。

```text
ethornell.exe --help
ethornell.exe list INPUT.arc
ethornell.exe extract INPUT.arc OUTPUT_DIR
ethornell.exe create INPUT_DIR OUTPUT.arc
ethornell.exe dsc-key ORIGINAL_DSC
ethornell.exe dsc-decompress INPUT_DSC OUTPUT_FILE
ethornell.exe dsc-compress INPUT_FILE OUTPUT_DSC KEY_HEX
```

- `list`：stdout 为 JSON 数组，字段 `name`、`offset`（归档内绝对字节位置）、`size`。不解压 DSC。
- `extract`：原样提取归档条目；不执行 DSC 解压或音频转换。输出目录必须不存在或为空。
- `create`：递归收集目录文件，使用相对路径、Shift-JIS 文件名和 ARC20 布局；输出路径完全按参数使用，不自动添加 `.new`。不自动压缩 DSC。输入路径名编码后不得超过 95 字节；不截断名称。空目录不入包。
- `dsc-key`：stdout 为 JSON 对象，含 `key_hex`、`original_size`、`symbol_count`。密钥来自原始 DSC；不要猜测或套用其他条目的密钥。
- `dsc-compress`：`KEY_HEX` 为 8 位十六进制，可带 `0x`。压缩器为 Python 实现，大文件可能较慢。
- 三个输出文件命令拒绝覆盖已有文件；自行选择新的输出路径。输出父目录会自动创建。
- 成功返回 0，参数错误返回 2，运行错误返回 1；错误写 stderr。检查退出码及产物，不能仅凭日志判断完成。
- 只支持 ARC20；不支持旧 `PackFile`、BSE 加密资源处理或通用脚本文本/语音映射。DSC 与 ARC 是独立层级。
- 重建后提取到另一空目录，逐条比较名称与 SHA-256。保留原始压缩 DSC 与密钥。归档内容验证不替代游戏内测试。

分发时完整保留 `tools/ethornell/`，包括 `.exe`、`_internal/`、许可证及 `source/` 中的对应源码。
