# WARC 与 Liar-soft 汉化包装验证

2026-11-19，串行复验三款游戏。使用独立目录导出原样逻辑成员，再用相应格式检查。样本专用的程序定位、参数和产物保留在本地工作目录。

| 游戏 | 归档与工具 | 已验证 | 尚待验证 |
| --- | --- | --- | --- |
| 花与乙女的祝福 | HANAOTOC_S.WAR，WARC 1.7，GARbro Mod 1.0.2.2 配合原版程序的 YPK 预处理参数 | **6/6 SCN**，合计 494,088 字节。每条 zlib 流完整结束并通过 Adler-32，输出长度与索引一致 | SCN 指令及对白语义、其他包和 BIN 的剩余成员 |
| 赫炎的印加诺克 Full Voice ReBORN | 汉化 XFL，MoleBox 2.x 包装，IDEA 变换 | **688/688**，目录 MD5 通过。包含 399 GSC、284 WCG、3 LWG、2 MPG。399 个 GSC 全部以 GBK 导出 TSC | 汉化覆盖关系、剧情路线与运行时加载 |
| 漆黑的夏尔诺斯 Full Voice ReBORN | 汉化 XFL，MoleBox 2.x 包装，64 位查表变换 | **1,154/1,154**，目录 MD5 通过。包含 159 GSC、989 WCG、4 LWG、2 MPG。159 个 GSC 全部以 GBK 导出 TSC | 汉化覆盖关系、剧情路线与运行时加载 |

MoleBox 两包逐项核对目录路径、分块范围和逻辑长度。zlib 块另校验完整流及 Adler-32。已复核 GSC 分段范围及 WCG、LWG、MPG 文件头。GSC 导出使用 LiarsoftTool v2.3.1。封包与游戏内加载待验。 [MoleBox 2.x 提取器源码](https://aluigi.altervista.org/papers/molebox2ext.zip) · [LiarsoftTool v2.3.1](https://github.com/Love-in-idleness/LiarsoftTool/releases/tag/v2.3.1)

[上一轮归档复验](continuation-validation-2026-11-19.md) · [2026-11-20 剧情、回封与加载续测](warc-xfl-scenario-validation-2026-11-20.md)
