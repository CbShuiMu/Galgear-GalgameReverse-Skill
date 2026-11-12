# rUGP RIO 目录 CLI

入口为 `python tools/age-rio-cli/rio_inventory.py`，使用 Python 3.10+ 标准库。来源为 [AgeReVerse](https://github.com/RepressedAlliance/AgeReVerse)，固定提交 `17618428499e90aa9b971212f7167cfdaf09912b`；保留完整单文件源码、MIT 许可和 `provenance.json`。源码内同时保留所移植 GARbro 目录读取实现的许可声明。

```powershell
python tools/age-rio-cli/rio_inventory.py --ici D:/Games/Example/game.rio.ici --main-rio D:/Games/Example/game.rio --volume D:/Games/Example/game.rio.002 --kind image --output D:/GalWork/Example/image-inventory.json
```

先执行 `--help` 检查参数。`--volume` 可重复，额外卷绑定形式以当前帮助为准。默认输出 JSON；`--format csv` 可输出 CSV。所有游戏输入只读，报告使用新的独立输出路径。

输出含对象类、卷名、全局及卷内偏移、声明范围和边界检查。`--kind image` 只是按对象类筛选元数据，**不会提取、解密或解码图像载荷**。目录名称可能尚未还原；`extent` 和图像类标签也不能直接作为完整图像或差分组合成功的证明。缺卷、未知类和目录警告保留到项目记录。

目录登记的 CRsa 可交给 [脚本载荷 CLI](rugp-crsa.md)。部分图像载荷、PNG 与静态 RUO 往返使用 [图像／RUO CLI](rugp-images.md)。见 [rUGP 资料](../engine/rugp.md) 和 [CG 状态表](../catalog/cg-status.md)。
