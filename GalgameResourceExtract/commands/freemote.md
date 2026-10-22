# FreeMote CLI：PSB / SCN 与 MDF

随附 `tools/freemote/PsbDecompile.exe` 和 `tools/freemote/PsBuild.exe`，需要 Windows 与 .NET Framework 4.8；无需 GUI、Python 或现场编译。工具目录只有命令行程序、配置、所需托管 DLL、来源与许可证。已排除 Viewer、EmtMake、EmtConvert、Emote 渲染器及外部转换插件；不因帮助仍列出其他类型就承诺相关插件可用。

来源为 [FreeMote v4.9.0](https://github.com/UlyssesWu/FreeMote/releases/tag/v4.9.0)，固定提交 `d87be1f3b8458c81822825fd6d56123d4df860b4`；发布压缩包 SHA-256 为 `831fe10f2afe0b630dcd16b55078a79a8990b22470bf5dc4fc1a13b96ff915eb`。`SOURCE.json` 记录保留文件哈希及裁剪范围。保留 `FreeMote.LICENSE.txt`、`LICENSE` 与 `licenses/`；FreeMote 为 CC BY-NC-SA 4.0，部分转换输出同受该许可约束，依赖保留各自许可。

| 操作 | CLI | 验证范围与限制 |
| --- | --- | --- |
| 帮助 | `PsbDecompile.exe --help` / `PsBuild.exe --help` | 标准命令行入口，不启动 Viewer |
| 导出原样资源块及 JSON | `PsbDecompile.exe -raw -t Scn -o WORK INPUT.scn` | `-t` 仅在格式证据已确认时指定；保留 `.json`、`.resx.json` 及其完整资源目录 |
| 重建未包装 PSB | `PsBuild.exe -ns -o OUTPUT.scn WORK/INPUT.json` | 沿用配套 `.resx.json` 的版本、平台和资源关系；`-ns` 仅在目标需要无壳时使用 |
| 保留原壳重建 | `PsBuild.exe -o OUTPUT.mdf WORK/INPUT.json` | 不加 `-ns`，由配套上下文恢复已支持的壳；已测普通 MDF，未知壳不能自动降级 |
| 显式版本/平台 | `PsBuild.exe -v 3 -p win -ns -o OUTPUT.scn INPUT.json` | 仅在原始格式要求已确认时覆盖；不能把工具默认值当作目标游戏设置 |

用新工作目录和新输出文件路径调用；上游 `-o` 可覆盖目标，先检查目标不存在，不对原件执行。泛型 PSB、SCN、图像和音频各有类型处理器；不要为绕过错误强制设成另一类型。遇到 `resource is not used`、资源数/长度变化、缺少插件或读取异常时，不交付重建结果，保留原件并核查类型和资源绑定。退出码之外还须检查日志和实际产物。

JSON 往返可能重排底层 names、字符串或对象表；整体文件哈希变化时，按原始引用关系核对结构语义与每个原样资源块，不能仅凭重新导出成功验收。合成测试中的规范输入可逐字节重建，不将此结论推广到任意原始 PSB。

当前裁剪包含内置 MDF/zlib 及原样二进制块路线，不含 TLG、WebP、FastLZ、LZ4、MZS、PSD 等外部插件转换。已有压缩图像或音频可作为原样块保留，不能假称已经支持对应媒体重编码。密钥、特殊字符编码与专用壳参数只在当前项目确认，不写成 Emote 默认值。

验证等级为合成：从隔离安装目录实际运行两个 CLI，测试 PSB v2/v3/v4 的 SCN 字符串、数值、原样资源块与逐字节往返，以及 v3 普通 MDF 的解包和重新包装。没有真实游戏、未知 PSB 类型或专用加密壳验证。外层 XP3 等归档仍由对应归档工具处理。
