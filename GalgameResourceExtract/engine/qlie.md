# QLIE：FilePack、场景文本与 DPNG

## 解包与封包工具

| 工具与来源 | 解包或读取 | 封包 | 适用范围 |
| --- | --- | --- | --- |
| 随附 [GARbro Mod](../commands/garbro.md) | 读取实测的 FilePack 1.0、3.0 和 3.1，按成员名抽提 | 未验证 | 按包核对目录和成员 |
| 随附 [图像 CLI](../commands/garbro-images.md) | 将已提取的 DPNG 等成员解码到独立目录 | 未验证 | 保留原生资源及图块 |

## 格式特征与编码

从文件末尾 28 字节核对 `FilePackVer`、版本、条目数和索引偏移。文件首部可能是成员数据，同一版本也可能有多个目录布局，尤其是 1.0。按实际成员名与边界核对。 [固定版 FilePack 读取器](https://github.com/crskycode/GARbro/blob/102d19710c819ed363b7ea28f2d883ccaf922214/ArcFormats/Qlie/ArcQLIE.cs)

`.png` 可实际为 DPNG，`.b` 可实际为 ABMP。DPNG 的表包含画布、图块坐标和负载大小。保留原生文件，解码结果另存。跨成员差分和动画顺序需要场景引用。 [固定版 DPNG 读取器](https://github.com/crskycode/GARbro/blob/102d19710c819ed363b7ea28f2d883ccaf922214/ArcFormats/Qlie/ImageDPNG.cs)

## 场景与补丁

实测脚本同时出现 UTF-16 BOM 和无 BOM 的旧编码。两种编码均可严格解码时，还需对照场景命令与已知文本。保留原始字节和包来源。有同名 `.s` 时按包保存。记录 `^include`、`^select` 和跳转候选的行号，核对指令语义与覆盖优先级后再合并。没有 FilePack 包尾的 `.dat` 补丁独立识别。

<!-- EXPERIENCE:50b4db5cbd05dc1818a5bb0bfc3b924cb9aee6af634a848566ba6f10e773c153:START -->
## 按包尾识别 QLIE 并核对 DPNG

- 引擎版本：FilePack 1.0 / 3.0 / 3.1
- 方言/条件：Windows 安装实测，以固定版本及样本的边界检查为准
- 阶段：extract
- 验证等级：real_sample
- 经验 ID：`50b4db5cbd05dc1818a5bb0bfc3b924cb9aee6af634a848566ba6f10e773c153`

本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。

### 适用前提

- 包尾包含受支持的 FilePack 版本和有界索引

### 已验证步骤

- 使用 Mod 分包比对索引和抽提结果。识别 DPNG 签名及图块范围，并用同版图像读取器生成独立 PNG

### 限制与失效条件

- 各版脚本编码、补丁优先级、跨资源差分和封包分别核对

原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。
<!-- EXPERIENCE:50b4db5cbd05dc1818a5bb0bfc3b924cb9aee6af634a848566ba6f10e773c153:END -->
