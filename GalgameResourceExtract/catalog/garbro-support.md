# GARbro 对常见 GalGame 引擎的解包支持情况

GARbro 不能全部覆盖。它支持下表中大部分引擎的常见资源归档，但不保证支持每个游戏、版本和加密变体。**能解包不等于能把脚本转换成可读文本。**

以下以原版 [morkt/GARbro](https://github.com/morkt/GARbro) 为准，第三方修改版可能不同。

| 引擎 | GARbro 解包支持情况 | 限制 |
|---|---|---|
| KiriKiri／KAG | ✅ 支持常见 `.xp3` | 特殊加密可能需要对应游戏配置，或无法打开 |
| NScripter | ✅ 支持 `.nsa`、`.sar` | `nscript.dat` 的脚本解码需要另行处理 |
| ONScripter 及衍生版 | ✅ 支持常见 `.nsa`、`.sar`、`.ns2` | 衍生版自定义封包不保证兼容 |
| RealLive | ⚠️ 支持 `.ovk`、`.nwk`、`.koe` 等语音包 | 不应据此认为所有 `SEEN.TXT` 脚本包都支持 |
| SiglusEngine | ⚠️ 支持部分共用音频格式 | 原版未提供通用的 `Scene.pck` 解包支持 |
| CatSystem2 | ✅ 支持常见 `.int` | 可能需要游戏密钥；提取 `.cst` 后仍需专用脚本工具 |
| YU-RIS | ✅ 支持常见 `.ypf` | 提取出的 `.ybn` 仍是编译脚本 |
| BGI／Ethornell | ✅ 支持常见 `.arc` | 剧情脚本仍需专用工具解析 |
| Majiro | ✅ 支持常见 `.arc` | `.mjo` 反汇编需使用 Majiro 工具 |
| WillPlus／AdvHD | ⚠️ 支持部分 Will 系列 `.arc` | 不保证覆盖所有 AdvHD 变体；`.ws2` 解析需专用工具 |
| Ren’Py | ✅ 支持常见 `.rpa` | `.rpyc` 反编译是另一项操作；定制封包可能不兼容 |
| TyranoScript／TyranoBuilder | ⚠️ 没有统一的引擎专用解包支持 | 散文件通常无需解包；桌面应用封装需按实际容器处理 |

## 支持范围说明

常见封包支持可对照 [GARbro 官方格式列表](https://morkt.github.io/GARbro/supported.html)。该列表中的游戏名称表示已测试作品，不代表同一引擎的所有作品均可解包。

RealLive 音频包支持可见 [OVK／NWK 实现](https://github.com/morkt/GARbro/blob/master/ArcFormats/RealLive/ArcOVK.cs)；其 [SEEN 实现](https://github.com/morkt/GARbro/blob/master/ArcFormats/RealLive/ArcSEEN.cs)标注的是 AVG32 脚本包，不能泛化为全部 RealLive 脚本。

## 按目标资源选择后续处理

GARbro 可以承担很多游戏的资源解包。只需原样文件时，核对所选条目和提取结果即可；需要可读脚本、图像或音频时，再按目标选择解析或转换工具。需要对白与语音关联时，还须使用引擎脚本解析工具证明引用关系。

- 资源解包：从归档中提取脚本、图像和音频等文件。
- 资源转换：按用户需要处理工具支持的图像或音频格式，转换结果与原样基线分开。
- 脚本解析：读取编译脚本中的目标结构；需要对白与语音关联时再解析角色和语音调用。
- 音频解码：将专用音频格式转换为常用格式；提取文件不一定包含这一步。
- 对白与语音关联：根据脚本中的语音调用建立对应关系，不能仅凭文件名排序确定。
