# SiglusEngine：Scene.pck、场景 DAT 与独立媒体资源

## 解包与封包工具

| 工具与来源 | 解包或读取用途 | 封包或回写用途 | 适用版本与限制 |
| --- | --- | --- | --- |
| [Siglus CLI：归档适配](../commands/siglus-ssu.md)，随附工具 | `unpack` 从支持的 `Scene.pck` 提取已解压、解密的场景 DAT | `pack --base` 按原包身份替换 DAT，保留包级属性、命令表与未修改成员的原压缩字节 | 已知 92 字节 PCK 头、连续场景数据布局；带嵌入源码时只允许未修改场景往返，拒绝新 DAT 与旧源码不符。未知布局直接报错 |
| [SiglusSceneScriptUtility 0.5.7][upstream]，随附在同一 CLI | 上游 `-x` 解包并尝试恢复嵌入源码，`--disam` 反汇编；`--decompile` 为实验性反编译 | `-c` 从完整源码编译；`-c --dat-repack` 从现有 DAT 新建场景包 | 上游提供多个指令版本配置；缺少 `.inc` 时 `--dat-repack` 不能恢复原包的 include 元数据。不能用实验性反编译输出替代可靠的重建基线 |
| [GARbro CLI](../commands/garbro.md)，随附工具 | 按实际格式识别其支持的图像、语音包和其他归档 | 仅适用于可写列表中的其他外层格式 | 不能用其他可写格式改扩展名代替 `Scene.pck`；特定媒体解码能力不等于场景归档写入能力 |

两个技能均独立随附 Windows x64 CLI，内含 Python 运行时，无需联网或安装 Rust。来源、许可、纯 Python 源码和构建方法见工具目录；图像编辑所需的可选 Pillow、诊断用 psutil 与 Rust 加速未随附，不把这些可选功能记为已验证能力。

## 格式特征与编码方式

| 格式或层级 | 通用识别特征 | 编码方式与判定依据 |
| --- | --- | --- |
| `Scene.pck` 场景归档 | 所引实现按小端整数头读取 include 属性/命令表、场景名表及场景数据索引；常规头长 92 字节，没有可通用于所有 PCK 的文本 magic | 场景名和包级名称按 UTF-16LE 还原；索引偏移与名称长度的单位分别核对，名称索引长度按 UTF-16 代码单元计算。文件名 `.pck` 也可能属于其他格式；见[头字段][const]和[写入实现][linker] |
| 场景 DAT | 已解码的常规场景头长 132 字节，包含字节码范围、字符串索引、标签及属性等分段信息 | 字符串内容按 UTF-16LE 处理，字符串表另可有按索引派生的 XOR；应先确认版本配置、变换和段边界，再读取文本。不能把整个 DAT 当作 UTF-16LE 文本；见[场景读取][dat] |
| 场景压缩与加密 | 外层成员可原样保存，也可使用所引实现的 LZSS 与公共 XOR，另有由 PCK 头标记的项目附加 XOR 层 | 压缩和加密是独立字节变换，不是字符编码。项目密钥从当前用户授权输入中确定，技能包不收录游戏密钥；见[场景解码][pck] |
| `Gameexe.dat` 与工作源码 | 是独立配置内容，不能因扩展名 `.dat` 而作为场景 DAT 封包 | 配置有自己的头部、压缩和变换规则；工作源码可由工具按明确的 `--charset` 处理，该选项不证明运行文件使用同一编码；见[配置实现][gei] |
| G00、NWA、OVK / OWP、OMV 等媒体 | 资源分别检查文件头、索引和内部条目，不能从 `Scene.pck` 推断其版本 | 图像压缩、音频编码与视频编码分别按各自读取实现确定。语音包中的条目编号与脚本语音参数需要实际关联验证；见[上游手册][manual] |

适用版本与验证等级：实现来源固定为 SSSU `0.5.7` / 提交 `85700715aed8695a95183bb973f981a61ae9d9c7`。上游有常规、旧版及移动版配置，归档适配不据此宣称覆盖全部配置；本仓库只验证合成 DAT/PCK 的压缩与原样往返、非空 include 元数据保留、条目身份和拒绝条件，没有真实游戏运行验证。头部尺寸、索引单位、段边界、字符串变换或指令表不符时停止套用。

## 注意事项

### 保存归档基线与包级元数据

`unpack` 输出的是已解码场景 DAT，嵌入源码继续保留在原始 PCK；这只是场景工作目录，不能单独宣称是整个原包的原样资源根目录。需要全部成员时，另用上游 `-x` 恢复其支持的嵌入源码，并始终保存原始 PCK。`pack --base` 要求原场景完整保留，拒绝新增、缺失、重复身份、目录链接及不支持的布局。

包级 include 属性和命令表不能只从场景 DAT 文件名恢复。归档适配直接保留原表，适用于只替换现有场景的任务；新增场景、改变跨场景命令或重新链接需要完整可靠源码与版本匹配的编译流程。带嵌入源码时修改 DAT 会使下一轮提取还原出旧源码，因此适配入口默认拒绝该情形。

### 版本配置与字符串变换

上游配置表区分官方版本与重建配置，不能因为工具默认配置可输出文字就认定指令语义正确。先用同版本读取或编译证据确认配置；旧版本存在明文 UTF-16LE 字符串表分支，字符编码和字符串 XOR 两层仍需分别判定。不把一款作品的 `--string-xor-multiplier`、密钥或汉化编码写成引擎默认值。

### 验证边界

封包后重新解包，比对全部场景身份、数量与 DAT 哈希；还要核对 include 表和原包中其他必须保留的内容。脚本反汇编、对白解析、对白与语音关联及游戏运行验证各自记录结果，不能用归档往返成功证明下一层语义正确。执行编译或资源工具不自动包含启动游戏或修改引擎程序的授权。

[upstream]: https://github.com/Jirehlov/SiglusSceneScriptUtility/tree/85700715aed8695a95183bb973f981a61ae9d9c7
[manual]: https://github.com/Jirehlov/SiglusSceneScriptUtility/blob/85700715aed8695a95183bb973f981a61ae9d9c7/manual.md
[const]: https://github.com/Jirehlov/SiglusSceneScriptUtility/blob/85700715aed8695a95183bb973f981a61ae9d9c7/src/siglus_ssu/const.py
[linker]: https://github.com/Jirehlov/SiglusSceneScriptUtility/blob/85700715aed8695a95183bb973f981a61ae9d9c7/src/siglus_ssu/linker.py
[dat]: https://github.com/Jirehlov/SiglusSceneScriptUtility/blob/85700715aed8695a95183bb973f981a61ae9d9c7/src/siglus_ssu/dat.py
[pck]: https://github.com/Jirehlov/SiglusSceneScriptUtility/blob/85700715aed8695a95183bb973f981a61ae9d9c7/src/siglus_ssu/pck.py
[gei]: https://github.com/Jirehlov/SiglusSceneScriptUtility/blob/85700715aed8695a95183bb973f981a61ae9d9c7/src/siglus_ssu/GEI.py
