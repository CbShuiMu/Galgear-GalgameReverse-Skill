# MUSICA SC 的字段编码与静态位置

以同一版本的原样 SC 建立控制流基线。识别 `.message` 字段后，分别验证正文、姓名和语音引用。跨版本对齐使用脚本名、消息号、语音引用和同号出现次序，再逐字节比对姓名。局部文本用另一字符集后仍可能通过整文件解码，逐字段验证可以发现这类混合编码。[固定版字段参考](https://github.com/arcusmaximus/VNTranslationTools/blob/36fbe909d02f2e9bb187443e03e2df595f56bfec/VNTextPatch.Shared/Scripts/MusicaScript.cs)

以文件哈希、行号和字节偏移回指脚本。核对 `.if` 的顺序后继与标签目标、`.goto` 的局部标签、`.chain` 的目标脚本和加载来源。只在明确提供配套原版时补查附加包缺失的链目标。GalExtract 随附 `scripts/parse_musica_sc.py`。

`prohibitAutoSave` 和 `prohibitSaveLoad` 等写入可定位脚本中的开关。定位真实存档还需配对存档字节、运行场景和恢复位置。存档样本及运行跟踪单独保存在项目工作区。

<!-- EXPERIENCE:8e41531f55d1b515fa6800f011b684f093541786ece2efba8a31668ff53ca491:START -->
## 跨版本对齐 SC 消息以验证字段级编码

- 引擎版本：MUSICA SC
- 方言/条件：Windows，限匹配脚本布局
- 阶段：reverse
- 验证等级：real_sample
- 经验 ID：`8e41531f55d1b515fa6800f011b684f093541786ece2efba8a31668ff53ca491`

本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。

### 适用前提

- 有可核对的原版与补丁 SC，并可定位实际消息与语音字段。

### 已验证步骤

- 按脚本、消息号、语音引用和同号出现次序比对原始字段字节；回指标签、顺序后继及跨文件目标。

### 限制与失效条件

- 静态坐标只覆盖显式分支，真实存档位置及运行路径另验。

原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。
<!-- EXPERIENCE:8e41531f55d1b515fa6800f011b684f093541786ece2efba8a31668ff53ca491:END -->
