# EntisGLS_Tools 源码摘录

以下文件来自 Crsky 的 [EntisGLS_Tools](https://github.com/crskycode/EntisGLS_Tools/tree/ccc67f537f56302fedae91b12ad8eff5ce8b4d62)，固定提交为 `ccc67f537f56302fedae91b12ad8eff5ce8b4d62`。源码内容保持上游原样，随附完整的 [GPL 第 3 版许可证](LICENSE.txt)。本说明只维护来源及当前文档路径。

这些文件用于核对字段布局，不是完整的可执行解析器；源码内部相对目录保持不变：

- `CSXToolPlus/Types/FileHeader.cs`：64 字节文件头。
- `CSXToolPlus/Sections/SectionConstString.cs`：字符串表计数与条目。
- `CSXToolPlus/Types/ConstStringEntry.cs`：字符串及其引用，包括空字符串。
- `CSXToolPlus/Types/DwordArray.cs`：引用计数与 32 位元素。
- `CSXToolPlus/Extensions/BinaryReaderExtensions.cs`：UTF-16 代码单元长度。

段遍历和指令处理参见 [Entis GLS / Cotopha 引擎资料](../../engine/entis-gls.md) 中的固定版本来源。上游源码仅为其支持版本提供证据，不能据此确定任意游戏的资源加载优先级或存档状态布局。
