# 常见 GalGame 引擎与脚本、语音文件格式

格式以 PC 版常见情况为主，具体游戏可能因引擎版本、插件或加密方案而不同。

| 引擎 | 常见脚本格式 | 常见语音文件格式 | 常见封包／存放方式 | 说明与参考 |
|---|---|---|---|---|
| 吉里吉里 KiriKiri／KAG | `.ks`：剧情脚本；`.tjs`：程序逻辑 | `.ogg`、`.wav`；其他格式取决于插件 | `.xp3`，也可直接存放散文件 | 脚本可能经过加密；[KAG 文档](https://kirikirikag.sourceforge.net/contents/Prepare.html) |
| NScripter | `0.txt`、`00.txt` 等文本脚本；`nscript.dat`：编码后的脚本 | `.wav`、`.mp3`；`.ogg` 支持依版本而异 | `.nsa`、`.sar`，或散文件 | `nscript.dat` 不是普通文本；[命令参考](https://07th-mod.github.io/ponscripter-fork/api/) |
| ONScripter 及其衍生版 | `0.txt`、`00.txt`、`nscript.dat`；部分衍生版有其他形式 | `.ogg`、`.wav`、`.mp3` | `.nsa`、`.sar`、`.ns2`，或散文件 | 兼容 NScripter 脚本，衍生版支持范围不同；[官方说明](https://ogapee.github.io/www/onscripter_en.html) |
| RealLive | `SEEN.TXT`：脚本集合；内部为编译后的 `SEENxxxx.TXT` | `.ovk` 内为 Ogg；`.nwk` 内为 NWA；旧作还可能使用 `.koe` 语音包 | `SEEN.TXT` 存脚本；`.ovk`、`.nwk`、`.koe` 存语音 | `SEEN.TXT` 虽以 `.TXT` 结尾，实际是二进制；[RLVM 说明](https://github.com/eglaysher/rlvm/blob/master/README.md) |
| SiglusEngine | `Scene.pck` 内的编译场景 `.dat`；源码通常为 `.ss` | `.ovk` 内为 `.ogg`；另有 `.nwa`、`.owp` 等音频资源 | `Scene.pck`、`.ovk` 等 | `.owp` 可还原为 Ogg，`.nwa` 需解码为 WAV；[格式与工具说明](https://github.com/Jirehlov/SiglusSceneScriptUtility/blob/main/manual.md) |
| CatSystem2 | `.cst`：编译剧情脚本；`.fes`：界面脚本 | 常见 `.ogg`，也有 `.wav` | `.int`，如 `scene.int`、`pcm_*.int` | 语音常按角色分包；[格式说明](https://github.com/trigger-segfault/TriggersTools.CatSystem2/wiki/Category:-Guides) |
| YU-RIS | `.yst`：源码；`.ybn`：编译脚本，常有 `YSTB` 标识 | 常见 `.ogg`，部分使用 `.wav` | `.ypf` | 发布版通常需要先解包才能取得 `.ybn`；[引擎格式研究](https://github.com/shimamura-sakura/yuri/blob/main/yuri.md) |
| BGI／Ethornell | 常见无扩展名的二进制剧情脚本；`._bp`：系统脚本 | `.bw`、`._bw` 或无扩展名的 BGI 音频，内部可为 Ogg Vorbis | `.arc`，常见 `data*.arc` | 需按文件头识别；[脚本说明](https://github.com/KlparetlR/Bgi_asdis)、[音频格式实现](https://github.com/morkt/GARbro/blob/master/ArcFormats/Ethornell/AudioBGI.cs) |
| Majiro | `.mjo`：编译后的二进制脚本 | 常见 `.ogg`、`.wav`，以具体作品为准 | `.arc`，如 `scenario.arc`、`voice.arc` | 工具导出的 `.mjil`、`.mjres` 属于反汇编及文本中间格式；[MajiroTools](https://github.com/AtomCrafty/MajiroTools) |
| WillPlus／AdvHD | `.ws2`：编译剧情脚本；翻译补丁可有 `.lng` 表 | 常见 `.ogg`、`.wav`，以具体作品为准 | `.arc` | 不同版本结构可能不同；先核对[翻译表与说话人证据链](../engine/willplus.md)，同时检查原始脚本、姓名表及翻译归档 |
| Entis GLS／Cotopha | `.csx`：`Cotopha Image file` 二进制脚本；版本间可用内联字符串或 `conststr` 表 | 常见 `.mio` 等；以文件头和调用为准 | `.noa` 等 Entis 归档，也有散文件 | 先核验分层、16 字节段头和完整字符串索引；见[NOA、CSX 与 Cotomi 存档参考](../engine/entis-gls.md)。同名资源加载优先级须在当前安装验证 |
| Ren’Py | `.rpy`：源码；`.rpyc`：编译脚本 | 常见 `.ogg`、`.opus`、`.mp3`、`.wav`，也支持 `.flac` 等 | `.rpa`，或 `game/` 下的散文件 | 语音通常由 `voice` 语句或自动语音机制引用；[音频文档](https://www.renpy.org/doc/html/audio.html) |
| TyranoScript／TyranoBuilder | `.ks`：剧情脚本；`.js`：逻辑及插件 | `.mp3`、`.ogg`、`.m4a`、`.wav` | 通常在 `data/scenario/`、`data/sound/` 等目录；桌面版可能另行封装 | 实际音频支持取决于浏览器或桌面运行环境；[官方标签参考](https://tyrano.jp/tag/v5) |

## 使用说明

- `.xp3`、`.int`、`.ypf`、`.arc`、`.rpa` 是封包格式，不是音频编码格式。
- `.ovk`、`.nwk` 是语音集合包，通常需要提取其中的单条语音。
- `.txt` 不一定是纯文本，`.wav` 也不一定是未压缩 PCM；识别时应结合文件头。
- 表中的音频格式不代表文件一定用于配音；语音、BGM 和音效常共用格式，需要结合目录和脚本调用判断。

具体引擎资料通过 [格式索引](formats.json) 路由。索引中的 `reference_only` 仅表示有分析资料；`external_cli` 表示需要工具核对当前归档，不是所有版本已验证可用。脚本语义和语音关联单独验证。
