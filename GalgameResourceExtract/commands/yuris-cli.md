# YU-RIS 474 只读 CLI

入口 `tools/yuris-cli/yuris_cli.py` 只依赖 Python 标准库，输出必须不存在：

```text
python tools/yuris-cli/yuris_cli.py list INPUT.ypf index.json
python tools/yuris-cli/yuris_cli.py extract INPUT.ypf RAW_DIR
python tools/yuris-cli/yuris_cli.py script INPUT.ybn result.json --commands ysc.ybn --encoding cp932
```

目前严格限定 **YPF/YSTB/YSCM 474**。其他版本明确拒绝，不宣称全版本支持。归档读取按所实现的名称交换表和名称字节变换核对名称 CRC32，再校验成员 Adler32、位置和解压长度；返回未经脚本解码的原样成员，附完整清单和 SHA-256。拒绝越界、路径穿越及重复名称。单成员解压上限 64 MiB；本工具面向可装入内存的脚本归档，媒体大包另选流式读取器。

脚本读取器由同目录 `ysc.ybn` 的命令表确定消费者，不硬编码 WORD 的操作码。保留指令偏移、原始行号、属性描述符及原值。仅将确认的 WORD 原始字符串拼成消息组，提取可见内联姓名；EVAL/GOSUB 的附加文本、姓名和选项消费者保留未解决。IF/ELSE/LOOP 中的控制元数据与字符串地址分开保存，未将它们解释成完整分支图。推导的 XOR 需通过全部区段和实际操作数检查；缺少探测字段时拒绝读取。

独立 Python 实现依据 [GARbro ArcYPF.cs](https://github.com/morkt/GARbro/blob/b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0/ArcFormats/YuRis/ArcYPF.cs) 与 [VNTranslationTools v0.0.41](https://github.com/arcusmaximus/VNTranslationTools/tree/36fbe909d02f2e9bb187443e03e2df595f56bfec/VNTextPatch.Shared/Scripts/Yuris)，均为 MIT。对应源码、许可证和哈希随工具保留，详见 `tools/yuris-cli/provenance.json`。控制元数据另参考 [yuri 的布局分析](https://github.com/shimamura-sakura/yuri/blob/main/yuri/fileformat/ystb.py)；该仓库未标明许可证，其源码未收入工具包。

没有封包、脚本写入、条件执行或存档恢复能力。原版、补丁、语言和备份分别处理；成员提取成功不代表已覆盖有效加载脚本。

## YPF 263 旧版索引

另有 `tools/yuris-cli/ypf263.py` 读取独立 YPF 263 的已验证旧版布局。

```text
python tools/yuris-cli/ypf263.py list INPUT.ypf
python tools/yuris-cli/ypf263.py extract INPUT.ypf NEW_DIR
python tools/yuris-cli/ypf263.py extract INPUT.ypf NEW_STORED_DIR --stored
```

在文件头版本、SwapTable04 名称长度、索引完整消耗和载荷范围同时匹配时，用全部名称的 Adler-32 验证单一 XOR 参数。随后逐条对存储载荷计算 Adler-32，压缩成员另核对 zlib 终点和解码长度。名称、名称字节、偏移、大小、状态及 SHA-256 保存在 `manifest.jsonl`，成员按序号保存，避免重复或无法解码的名称覆盖。输出目录必须不存在；有失败返回 1。`--stored` 只验证并复制原始存储范围。

263 分支使用 32 字节头之后的索引长度及 Adler-32 名称值。474 CLI 的索引结束位置与 CRC-32 名称规则不能直接套用。263 入口仅解包，不解释 YBN 语义或写回。参考源码和许可在 [provenance.json](../tools/yuris-cli/provenance.json)。
