# RLdev SEEN 原样归档 CLI

入口为 `python tools/rldev-seen/rlseen.py`，相对于本技能根目录；需要 Python 3.9+，仅使用标准库，无 GUI。版本 `rlseen 1.0`，根据 [RLdev archiver.ml](https://github.com/eglaysher/rldev/blob/074c8b1aa81f3fe7ce71a36be3408082f3d4fc20/src/kprl/archiver.ml) 的 SEEN 索引与原样成员逻辑适配，GPL-2.0-or-later。固定来源、原始源码与许可证随工具保留。

| 命令 | 用途与边界 |
| --- | --- |
| `rlseen.py list SEEN.TXT` | 校验 10000 个小端 offset/length 索引槽，输出 JSON 清单 |
| `rlseen.py unpack SEEN.TXT members` | 按原生槽号提取 `SEEN0000.TXT`–`SEEN9999.TXT`，保持归档成员字节 |
| `rlseen.py pack members rebuilt/SEEN.TXT` | 从完整原样资源根目录重建索引及成员，保留编号空洞；不解压、不加密、不编译脚本 |
| `rlseen.py --max-bytes 2147483648 unpack SEEN.TXT members` | 修改归档及累计提取大小上限，默认 1 GiB；格式仍受 32 位偏移限制 |

输入目录只接受直接下属的 `SEENnnnn.TXT`；其他文件、子目录、链接、重复编号和空成员会报错，避免静默遗漏。输出路径必须不存在；先验证索引与边界，再写临时产物，成功后发布。未知格式、越界和部分重叠索引拒绝处理。`0` 表示成功，`1` 表示数据或 IO 错误，参数错误返回 `2`。

本工具填补 SEEN 归档层双向读写，不替代完整 RLdev 的脚本反汇编、压缩与重新编译。RLdev 的 `KPRL`/`RDRL` 等解压工作文件会被拒绝封包，须先按原编译器版本正确恢复；特殊脚本密钥留在项目本地。重新解包后核对条目身份、数量与字节，脚本语义和游戏运行另验。

验证等级为合成：已测编号空洞、原样成员往返、越界、重复/异常文件和已有输出拒绝；不声明真实游戏兼容性，也不支持 AVG32 的其他 PACL 布局。
