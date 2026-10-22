# BGI / Ethornell：ARC 与 DSC

## 解包与封包工具

| 工具与来源 | 解包或读取用途 | 封包或回写用途 | 适用版本与限制 |
| --- | --- | --- | --- |
| [Ethornell CLI](../commands/ethornell.md)，随附，源于 [ethornell-tools][eth-tools] 与本地 CLI 入口 | 列表、原样提取 `BURIKO ARC20` 条目；独立读取 DSC 元数据、解压 DSC | 创建 ARC20；对已确认的 `DSC FORMAT 1.00` 流重新压缩 | 不支持旧 `PackFile` 封包，也不支持 BSE 处理；ARC20 创建不会自动压缩 DSC。文件名按 Shift-JIS 处理，最多 95 编码字节；参数及退出码见命令页 |
| [GARbro CLI](../commands/garbro.md)，随附，标签 `BGI` / `BURIKO ARC` | 读取旧 PackFile 和 ARC20；读取过程中可展开 DSC，或按已实现分支还原 BSE 头部 | 没有对应归档写入器 | 读取 BSE 仅覆盖所引实现中的 `1.00` / `1.01` 分支；不是所有 BGI 加密资源的通用方案；见[实现][bgi] |
| [Bgi_asdis][bgi-asdis]，外部，未随附 | 按剧情 v0/v1 和 BP 系统脚本分流做反汇编及文本读取 | 相应脚本汇编与文本导回；不负责 ARC 封包 | 使用对应版本操作码和完整依赖；不能把工具支持多种编码理解为引擎默认支持这些编码。脚本与归档独立验收 |

## 格式特征与编码方式

| 格式或层级 | 通用特征 | 编码方式与判定依据 |
| --- | --- | --- |
| 旧 PackFile 归档 | `PackFile` 及空格填充标识，条目数后接固定记录；所引读取器每条记录 32 字节、名称字段 16 字节 | 名称读取方式见[实现][bgi]；与 ARC20 分流，不仅凭 `.arc` 选择布局。名称解码和内部脚本文字分别验证 |
| ARC20 归档 | 十二字节 `BURIKO ARC20` 标识、条目数、每条 128 字节索引；名称字段 96 字节，条目偏移相对内容区 | 随附 Ethornell CLI 用 Shift-JIS 处理名称并保留成员存储字节；该编码只说明此工具的目录名称边界，不代表全部 BGI 正文编码 |
| DSC 压缩流 | `DSC FORMAT 1.00\0` 标识，包含原始大小、符号数及用于表还原的参数 | Huffman 表及回溯复制共同完成解压；DSC 是成员层压缩/字节处理，不是字符编码。重压缩按原 DSC 元数据取参数，不复制其他成员的值；见[实现][bgi]和[上游工具][eth-tools] |
| BSE 包装 | `BSE 1.` 标识；版本化头部在内容前 | 所引 GARbro 对已知版本还原 64 字节头部，再与主体连接。BSE 与 DSC 是不同层级，必须确认当前组合；随附 Ethornell CLI 不会自动完成它 |
| 剧情脚本与 `._bp` | 常见无扩展名二进制剧情脚本，以及独立 BP 系统脚本 | 先按版本、表头、操作码和字符串引用解析；所引[脚本工具][bgi-asdis]提供分版本读取并默认使用 Shift-JIS。当前项目仍须确认实际编码，不能把补丁、回退解码或工具可选编码收录为引擎默认 |
| BGI 音频 `bw` | 所引读取器检查偏移 4 的 `bw  ` 标识，首 DWORD 指向媒体数据 | 此分支内部为 Ogg/Vorbis；见[音频实现][bgi-audio]。提取原 `bw` 与导出 Ogg 分别保存，不能据扩展名将所有 BGI 音频视为这一分支 |
| CBG 图像及其他媒体 | 按 `CompressedBG` 等文件头和对应读取器识别 | 图像内部压缩、音频编码及视频容器独立于 ARC、DSC 和脚本文字，不统一转码基线 |

## 注意事项

需要用于重建的完整原样资源根目录时，ARC20 优先使用随附 Ethornell CLI 的原样提取路线。GARbro 的 `OpenEntry` 可能自动展开 DSC 或去掉 BSE 包装，不能把该结果误当作归档内存储层字节；记录每层输入输出，并保留原始归档与原 DSC。

修改 DSC 内部资源后，先重新压缩，再按 ARC20 创建流程封包。归档创建器不会替用户完成压缩、BSE、脚本汇编或媒体编码。需要 BSE 写回、旧 PackFile 封包或未知布局时，当前随附工具存在缺口，不能仅修改扩展名后继续。

先用代表性成员验证压缩后再次解压一致，再验证归档重新提取后的名称、数量与 SHA-256。压缩输出本身不必与原压缩流字节相同，但解压后的目标内容应一致；归档层的原样存储成员比较则必须使用同一层级。上述检查不替代加载器验证。

仅在用户需要结构化文本或对白与语音关联时，才进入脚本反汇编。保留函数、参数、控制码和字符串原位置，区分剧情、系统、选项与无语音文本。语音关系由实际调用证明，不使用固定 `data*.arc` 编号或文件排序推导。

## 来源、版本与验证边界

- GARbro 固定为 `b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0`（MIT）；本页只承诺所引读取分支。
- DSC 上游参考 `Jair4x/ethornell-tools` 固定为 `6bfdd2bce1041259439c9b18afe0be26a45c7676`；随附 CLI 的实际行为以[命令页](../commands/ethornell.md)和 `tools/ethornell/source/` 为准。
- 脚本资料固定为 `KlparetlR/Bgi_asdis` 的 `ba673164dd6c8effc4411664f246663c39f815b4`（MIT），只链接外部资料，不将其 GUI 或源码视为随附工具。
- 本页验证等级为文档与源码核对，没有使用原游戏验证。失效条件为签名、DSC 布局、BSE 版本、操作码或字符边界不匹配；特殊密钥、文件编号规律和本地化编码只在项目本地记录。

[bgi]: https://github.com/morkt/GARbro/blob/b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0/ArcFormats/Ethornell/ArcBGI.cs
[bgi-audio]: https://github.com/morkt/GARbro/blob/b09ee4570ccb1daf6ac56710ee8934dc0b8baeb0/ArcFormats/Ethornell/AudioBGI.cs
[eth-tools]: https://github.com/Jair4x/ethornell-tools/tree/6bfdd2bce1041259439c9b18afe0be26a45c7676
[bgi-asdis]: https://github.com/KlparetlR/Bgi_asdis/tree/ba673164dd6c8effc4411664f246663c39f815b4
