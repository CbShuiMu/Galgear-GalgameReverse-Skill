# rpatool CLI：Ren'Py RPA v2 / v3

入口为本技能内的 `tools/rpatool/rpatool.py`。需要 Python 3.9 或更新版本，仅用标准库；运行不依赖仓库根目录或其他技能。整目录保留相邻原始源码 `rpatool`、`LICENSE` 和 `SOURCE.json`。原始源码来自 [Shizmob/rpatool 0.8][upstream]，WTFPL-2.0；原项目本身就是 CLI，没有 GUI 文件。应使用适配入口，原始入口未修复多片段读取和索引执行问题。

## 命令

以下命令以本技能目录为工作目录，输入与输出路径可以是绝对路径。

```powershell
python tools/rpatool/rpatool.py --help
python tools/rpatool/rpatool.py --version
python tools/rpatool/rpatool.py list C:\Work\data.rpa
python tools/rpatool/rpatool.py extract C:\Work\data.rpa --output C:\Work\original-resources
python tools/rpatool/rpatool.py create C:\Work\staging --output C:\Work\rebuilt.rpa --format 3 --key 0xDEADBEEF
python tools/rpatool/rpatool.py create C:\Work\staging --output C:\Work\legacy.rpa --format 2
```

| 参数或行为 | 约定 |
| --- | --- |
| `list ARCHIVE` | 验证索引、名称和数据边界后，每行输出一个成员相对路径 |
| `extract ARCHIVE --output DIR` | 提取所有成员及所有片段，保留相对路径；原样资源根目录独立于解码或解析产物 |
| `create DIR --output FILE --format 2\|3` | 递归包含普通文件，保留相对路径，不保存空目录；默认写 v3。输出归档必须位于输入目录之外 |
| `--key INTEGER` | 仅创建时使用，支持 `0x` 十六进制；是 v3 索引 XOR 参数，不是媒体密钥。默认 `0xDEADBEEF`，v2 不使用该参数 |
| `--overwrite` | 提取、创建默认拒绝已有目标，明确提供时允许覆盖；创建先写临时归档，重新读取验证通过后替换输出 |
| `--max-file-mib N` | 每个成员的解包长度上限，默认 1024 MiB；三个子命令均可使用 |
| `--max-total-mib N` | 成员解包长度合计上限，默认 4096 MiB；三个子命令均可使用 |

成功返回 `0`，处理失败返回 `1`，参数错误返回 `2`；错误写到 stderr。解包会先检查全部条目再创建输出；磁盘或运行中 I/O 失败仍可能留下部分产物，必须按失败处理。创建复用上游内存写入器，输入总量与可用内存相称；提高大小限制不能提供流式封包能力。

## 支持范围与限制

- 只读取、创建标准 `RPA-2.0`、`RPA-3.0`；不将上游原脚本的 RPI / v3.2 能力当作适配入口能力。读取所有索引片段及可选前缀，按[官方 loader][loader]的 `prefix + length 个数据字节` 拼接。
- 索引是 zlib 压缩的 pickle。适配入口限制为基本数据类型，拒绝全局对象、持久对象和可执行构造指令；压缩与解压后的索引各最多 64 MiB，最多 100000 个成员、1000000 个片段。依赖 pickle 全局对象的变体会明确失败，不绕过限制执行包内对象。
- 成员文件名按 Unicode 或 UTF-8 字节读取；输出拒绝路径穿越、绝对路径、Windows 保留名称、大小写冲突、文件与目录冲突、符号链接及目录联接点。条目数据范围不能越过索引起点。
- 提取 RPA 不会把 `.rpyc` 变成 `.rpy`，创建 RPA 也不会编译脚本。脚本编译、反编译和媒体编码分别验证，脚本结构见 [Ren'Py 官方文档](https://www.renpy.org/doc/html/language_basics.html)。此 CLI 单独调用，不是 `resource_workflow.py pack/verify` 的后端。
- 所带测试仅用合成归档证明 CLI 行为，不证明目标游戏的脚本语义、加载顺序或修改兼容性。封包后独立提取到新目录，比较完整路径集合、数量和逐文件哈希，再按用户需要验证引擎。

固定来源、下载文件 SHA-256 和适配说明见 `tools/rpatool/SOURCE.json`。版本、pickle 布局、分段语义或加密方式不符时停止套用；特殊密钥、路径及游戏内容留在用户本地。

[upstream]: https://github.com/Shizmob/rpatool/tree/74f26d5dfdd645483e02552aa766ca447ad6b191
[loader]: https://github.com/renpy/renpy/blob/f5c62227489ba60939432f0a33dd7eceb6d83b54/renpy/loader.py
