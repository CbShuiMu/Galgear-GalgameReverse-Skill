# Artemis 存档索引只读 CLI

入口：`python tools/artemis-save/artemis_save_cli.py INPUT.dat OUTPUT.json`。只依赖 Python 标准库，输出必须不存在。默认解压上限 64 MiB，可用 `--max-bytes` 显式调整。

读取 BOWS/BOWG/BOWX 1002/1003 的 zlib 层和对象／字段二级索引，核对长度、索引尾指针、字段边界及重建索引与原 body 一致。匹配 root/caret 布局时导出 ASB 脚本名、命令序号及字段偏移；其他容器只报告索引结果。BOWG 全局数据不算剧情槽位。

该指针可能停在 `system/save.asb` 或 `system/script.asb`。它属于引擎的 ASB 执行层，不能直接当成上层 AST 剧情块。Lua 对象、回溯缓存、宏状态和 AST 关联尚未解释；没有实际加载验证。工具不执行 Lua，不修改存档。

上游为 [ns2-savekit](https://github.com/dougchansan/ns2-savekit/blob/656ce4d31fe569a7a22b7408d023c4326ce0880c/tools/artemis-save.py)，MIT。固定提交、源码和哈希见 `tools/artemis-save/provenance.json`；保留同目录 `LICENSE` 与 `source/artemis-save.py`。只读包装器不调用上游的编辑或启动功能。
