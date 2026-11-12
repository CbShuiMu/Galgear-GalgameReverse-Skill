# NeXAS PAC type 4：只读索引与成员提取

相对于技能根目录的入口为 `tools/nexas-pac4/pac4.py`，使用 Python 3 标准库。仅接受 `PAC` 前缀、成员方法 4、末尾反码 Huffman 索引及 76 字节记录的布局。格式依据、源码位置与 MIT 许可见 [SOURCE.json](../tools/nexas-pac4/SOURCE.json)。

```text
python tools/nexas-pac4/pac4.py list INPUT.pac
python tools/nexas-pac4/pac4.py --encoding gbk --recover-tail list INPUT.pac
python tools/nexas-pac4/pac4.py --encoding gbk --recover-tail extract INPUT.pac NEW_DIR
python tools/nexas-pac4/pac4.py --recover-tail extract INPUT.pac NEW_STORED_DIR --stored --entry 0
```

- `--encoding` 只改变显示名称解码。清单保留原名称字节、条目序号、偏移、存储大小和解码大小；解码失败时名称为 `null`。
- 默认遇到短索引即失败。`--recover-tail` 仅在 Huffman 缺失限定于最后一条存储长度的 1–3 个高字节时尝试恢复。前一段最后边界须紧接该条，推断区间延伸至压缩索引，且与已知低字节一致。清单把该条标为 `tail_size_inferred`，应另核对压缩流或媒体结构。
- 提取用序号命名，输出目录必须不存在，防止归档名称异常或同名覆盖。逻辑模式对大小不同的条目验证 zlib 终点及解码长度。`--stored` 保留归档内的原始字节范围。`manifest.jsonl` 记录成功、失败及 SHA-256，任一条失败返回 1。
- 封包、其他索引布局、其他压缩方法、脚本含义与存档恢复需另验。
