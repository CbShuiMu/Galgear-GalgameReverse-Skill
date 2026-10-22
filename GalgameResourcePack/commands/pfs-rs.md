# pfs-rs CLI 调用约定

用于 Artemis PF8/PFS 归档。入口为相对于本技能目录的 `tools/pfs-rs/pfs-rs.exe`；Windows x64，无 Rust、Python、GUI 或安装步骤。参数通过独立 argv 传递。

```text
pfs-rs.exe --help
pfs-rs.exe --version
pfs-rs.exe list INPUT.pfs
pfs-rs.exe list INPUT.pfs --long
pfs-rs.exe extract INPUT.pfs OUTPUT_DIR
pfs-rs.exe extract "INPUT_DIR/*.pfs*" OUTPUT_DIR --separate
pfs-rs.exe create INPUT_DIR/ --no-smart-detect -o OUTPUT.pfs
```

- `list` 输出供诊断的人类可读列表，不是 JSON；`--long` 加入大小信息。不要将表格当作稳定机器协议。
- `extract` 的通配符由工具展开，传入单个字符串。处理多个归档时使用 `--separate` 保留来源；避免不同归档同名条目互相覆盖。选择新的输出目录；不要复用有文件的目录。
- `create` 的尾部正斜杠 `/` 表示只封包目录内容；无 `/` 通常保留目录名。仅对单目录输入，包含 `system.ini` 时智能检测还可能自动剥离外层目录。为保持原始归档相对路径，使用 `INPUT_DIR/ --no-smart-detect`，不要将尾部 `/` 改为 `\`。
- 显式指定 `-o` 且选择不存在的路径；已有输出可能自动生成编号后缀。全局 `-f/--force` 会允许封包覆盖，不默认使用。提取流程并不使用该参数控制覆盖。
- 全局 `-C/--directory DIR` 在操作前切换工作目录；`-q/--quiet` 减少进度，日志仍可能输出；`-v/--verbose` 开启调试日志。无需使用无子命令的拖放模式。
- `--strip-components` 只有参数入口，当前实现不生效，不使用。
- 成功返回 0，运行失败返回非零；stdout/stderr 都可能有日志。核对退出码与实际输出路径。
- 归档层工具不负责解析 Artemis 脚本或生成对白映射。创建后重新提取，比较条目相对路径与 SHA-256。

分发时保留 `tools/pfs-rs/pfs-rs.exe` 及其 `licenses/` 目录。
