# GARbro 图像批处理 CLI

入口为 `tools/GARbro-cli/GalImageExport.exe JOB.json`，与现有 GARbro DLL、配置、`GameData/` 和许可证放在同一目录。需要 Windows 的 .NET Framework/WPF，无 GUI，不启动游戏。原生资源和 PNG 使用不同目录，输出目录必须不存在。

```json
{
  "mode": "archive",
  "source": "D:/Games/Example/images.arc",
  "output": "D:/GalWork/Example/images",
  "seconds": 240,
  "all": false
}
```

| 字段或模式 | 行为 |
| --- | --- |
| `archive` | 按 GARbro 的 `image` 类型和常用图像扩展名选择成员；先保留原样成员，再解码。`all: true` 只用于已确认的图像专用包，避免漏掉无扩展名的图像；不用于未识别的任意大包 |
| `files` | `source` 为父目录，`files` 为其下原生图像的绝对路径数组；复制后逐文件核对哈希，再解码 |
| `decode` | 与 `files` 同样输入，但复用已有原样资源路径，不重复复制；清单仍记录原文件身份 |
| `seconds` | 每个任务的处理预算，默认 240 秒。超时保留已完成结果并写延期记录；外部监督进程还应设置硬超时 |
| `filter` | 可选的 .NET 正则成员筛选；在上述类型选择之后执行，不会扩展到所有非图像条目 |
| `duplicatesOnly` | 默认 `false`。仅补提取同一归档中的后续同名成员时设为 `true`；成员序号仍按完整的筛选结果编号 |

`manifest.jsonl` 每条记录立即落盘。`raw` 记录原生逻辑成员路径、大小、SHA-256 和可用的归档位置；容器解压／混淆还原可能已由 GARbro 完成，完整原始归档仍应保留。`png` 记录尺寸、位深、偏移、输出哈希与来源；G00 v2、HG 等可识别的多子图容器另输出逐子图 PNG 和 `frame_container` 条目。帧的布局受对应读取器约束，不承诺还原任意 CG 叠放规则。

同一归档的后续同名成员写到 `__duplicate_members/<条目序号>/<原名>`，清单保留 `original_name`、`entry_index` 与 `duplicate_name`。不会因为名字相同覆盖前一个成员，也不按内容哈希删除成员。不同归档使用独立输出目录。

错误和延期分别记录为 `raw_error`、`decode_error`、`raw_deferred` 或 `decode_deferred`。退出码 0 只表示批处理流程结束，不表示每个成员成功；必须检查清单。退出码 1 为容器／任务失败，2 为参数或已有输出错误。截断清单、孤立的未登记文件和外部硬超时需要单独复核，不能只按目录文件数验收。

本工具不对资源去重、不猜测事件 CG、不改变透明度／差分组合、不封包。RCT/RC8、外部基图或标题专用解码依赖可能仍未完整满足；失败原生文件继续保留。完整 CG 验收见 [CG 提取流程](../guides/cg-extraction.md)。

新增批处理源码与编译脚本位于 `tools/GARbro-cli/source/`；来源和文件哈希见 `image-cli-provenance.json`。沿用 GARbro 1.5.44 的已安装读取库，保留 `GARbro-LICENSE.txt`。使用同目录 `source/build-images.ps1` 可重新编译本批处理入口，无须重建整个 GARbro。
