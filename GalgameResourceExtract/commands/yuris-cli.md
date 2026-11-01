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
