# GARbro Mod CLI：列表与解包

随附入口为相对于本技能根目录的 `tools/GARbro-cli/GARbro.Console.exe`，来自 [crskycode/GARbro 的 GARbro-Mod-1.0.2.2 发布包](https://github.com/crskycode/GARbro/releases/tag/GARbro-Mod-1.0.2.2)。需要 Windows、.NET Framework 4.7.2 及 WPF 运行库。该 CLI 与旧版命令不兼容，**不支持归档封包**；创建归档、旧版筛选及转换选项见 [GARbro 兼容后端](garbro-legacy.md)，图像批处理沿用其隔离运行库。

## 命令与输出位置

| 用法 | 行为 |
| --- | --- |
| `GARbro.Console.exe` | 无参数显示帮助；不要用 `h` 或 `--help`，它们会被当作文件模式 |
| `GARbro.Console.exe -l` | 列出当前运行库识别的归档格式；不表示这些格式可写 |
| `GARbro.Console.exe ARCHIVE` | 按偏移列出归档成员、大小及偏移 |
| `GARbro.Console.exe -x ARCHIVE` | 解包全部成员到进程当前目录 |
| `GARbro.Console.exe ARCHIVE ENTRY [ENTRY...]` | 按完整成员名提取指定条目；名称比较不区分大小写 |

`ARCHIVE` 可为绝对路径；带空格的路径和成员名加引号。参数按上表顺序传入。没有 `i/l/x/c/pack/options` 子命令，也没有 `-o`、`-q`、`-y`、`-s`、`-R` 或 `-O`。源码虽解析 `-c FORMAT`，没有使用该字段执行图像转换，不能据此宣称转换成功；使用已验证的图像 CLI 或兼容后端。

解包前解析 CLI 与归档绝对路径，新建一个不存在的输出目录，再将进程当前目录设为该目录。没有覆盖策略开关，不在原始资源、游戏安装目录或已存在的提取结果上运行。多归档任务逐包使用独立的原样资源根目录。

```powershell
# 从本技能根目录解析路径；将归档与输出示例替换为实际绝对路径。
$garbro = (Resolve-Path 'tools/GARbro-cli/GARbro.Console.exe').Path
$archive = (Resolve-Path 'D:\work\input\data.xp3').Path
$output = 'D:\work\raw\data'
& $garbro
& $garbro -l
& $garbro $archive
New-Item -ItemType Directory -Path $output -ErrorAction Stop | Out-Null
Push-Location -LiteralPath $output
try {
    & $garbro -x $archive
} finally {
    Pop-Location
}
# 此后按列表核对成员路径、数量和字节；不能只检查 $LASTEXITCODE。
```

## 完整性与失败判定

stdout 为帮助、格式列表、成员列表和解包进度，stderr 为读取或条目错误。此版本的 `Main` 返回 `void`，捕获异常后也可能返回退出码 `0`；文件模式无匹配时可能无输出。指定条目不存在、归档未知或数据库反序列化失败均须按实际日志和产物判为失败。不要把退出码或进度文字当成完整性证明。

核对归档成员与输出的完整相对路径、数量、大小及必要的哈希，报告缺失、冲突和未识别项。同名成员的逐项保留需另行处理。读取器可能解压或还原成员包装，保留原归档；脚本解析、对白与语音关联、媒体转换和游戏运行验证分别进行。

## 来源、依赖与验证边界

- 固定发布：`GARbro-Mod-1.0.2.2`；对应源码提交：`102d19710c819ed363b7ea28f2d883ccaf922214`。保留发布包中的 CLI、运行 DLL、配置、语言资源、`GameData/` 和 x86/x64 原生依赖；没有使用浮动分支数据库覆盖发布内容。
- 完整上游源码：[源码归档](../tools/GARbro-cli/source/GARbro-Mod-1.0.2.2.zip)；MIT 许可：[GARbro-LICENSE.txt](../tools/GARbro-cli/GARbro-LICENSE.txt)。依赖许可保存在 `tools/GARbro-cli/licenses/`。
- 来源 URL、发布包与源码 SHA-256、逐文件哈希、取舍清单和实际测试范围记录在 [provenance.json](../tools/GARbro-cli/provenance.json)。没有重编译上游 CLI 或运行库。
- `legacy/` 中的旧版 CLI、图像批处理及 DLL 保持独立；封包流程的 `--garbro` 指向其中的程序。不要将新版 CLI 传给只会发送 `c/x/-o` 的旧版调用器，也不要跨目录替换 DLL、配置或数据库。
- 验证使用临时目录和合成资源，覆盖两份技能独立复制后的帮助、格式列表、ZIP 列表与原样解包，以及既有封包、图像导出和独立读取检查。未启动真实游戏，未据此声明新增游戏兼容性。
