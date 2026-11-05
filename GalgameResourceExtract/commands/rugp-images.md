# rUGP 图像与 RUO CLI

入口为 `python tools/age-rio-cli/rugp_cli.py`，Python 3.10+ 标准库即可运行。源码固定到 AgeReVerse `17618428499e90aa9b971212f7167cfdaf09912b`；原样模块、MIT 许可和逐文件 SHA-256 随工具保留。无需启动游戏。

## 提取与差分

```text
python tools/age-rio-cli/rugp_cli.py scan D:/Work/candidates.json D:/Game/base.rio D:/Game/base.rio.002
python tools/age-rio-cli/rugp_cli.py extract D:/Work/candidates.json D:/Game D:/Work/native
python tools/age-rio-cli/rugp_cli.py decode-tree D:/Work/native D:/Work/png
```

所有输出必须不存在。先用 [RIO 目录 CLI](age-rio.md) 取得类名与精确范围；对目录未覆盖的区域，`scan` 可补充标准 Cr6Ti／CRip008 的头部候选。两者共有 `00 04 45`，必须进一步核对载荷长度位置、类型、尺寸、边界及尾部。扫描候选不是已恢复的目录或 CG 身份，不能直接据此添加引擎引用。

`extract` 只读取显式根目录内的来源，按来源文件、候选编号和物理偏移保存原样资源，记录 SHA-256，不按名称或相似度删除差分。`decode-tree` 逐条核对原样哈希，另存 PNG，清单包含画布、绘制矩形、偏移、透明及部分透明像素数量、像素哈希和失败项。每条立即落盘；批次有失败时仍保留成功记录，并返回非零退出码。图像候选可能是 UI、立绘、CG、子图或偶然匹配；解码通过也不证明剧情和图库覆盖完整。

Cr6Ti 使用严格封装检查与独立 native-reference 像素读取。kind 3 的共享差值和通道残差相加后再钳位，透明段须清除上一行预测状态；旧 v1 读取器读完码流仍可能产生错误颜色，不能仅用“生成 PNG”验收。实现选择的依据、真实样本边界见 [rUGP](../engine/rugp.md)。CRip008 仅接受上游已实现的 kind 2／3 与标志组合。CRmt 外部引用、CBg2d、其他未知类、全部场景叠放和名称恢复未由该扫描入口解决。

## 编码与静态回封

```text
python tools/age-rio-cli/rugp_cli.py encode-cr6ti D:/Work/template.bin D:/Work/edit.png D:/Work/replacement.bin
python tools/age-rio-cli/rugp_cli.py overlay D:/Work/replacement.bin D:/Work/combined.ruo1 --source-offset 0x1000 --unit 2 --base D:/Game/base.rio.ruo1
```

编码输入可为标准 RGB／RGBA PNG 或完整画布的 RGBA 字节。原样像素未变时保留模板原始记录字节；发生修改时由编码器生成，并用独立读取器比较全部像素。默认拒绝任何像素误差；只有显式 `--allow-quantization` 才允许有损候选，报告中的 `input_pixels_exact` 会如实为 false。上游编码器会量化通道与 alpha，不能将其内部读回一致等同于输入图像无损。

`--source-offset` 是原 RIO 逻辑对象的**全局字节偏移**，不是 PNG 位置或 RUO 中的目标偏移；`--unit` 必须来自当前 ICI／目录和实际 RUO 核验，不把示例的 2 套用到所有版本。写入器仅替换现有身份，未实现任意路径新增或完整 RIO／ICI 重建。调用前仍须确认对象身份；未绑定引用的扫描候选不自动成为可部署替换。

存在原 RUO 时生成一份累计 RUO：保留其完整数据区及未修改重定向，追加替换记录，按有符号源键排序并重新读取 footer、载荷和图像。不要直接安装多个独立 RUO 来假定可安全叠加。该命令输出旁路验证产物，不安装、不修改原游戏。静态 footer／字节／像素往返通过与游戏实际加载、显示、存读档各自验收。
