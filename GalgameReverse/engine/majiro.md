# Majiro 的跨脚本分派与存档位置

先核对 MJO 头中的主入口、函数哈希和字节码偏移。用操作数边界区分脚本跳转、函数调用与系统调用。若原生加载器会从参数中取文件基名后加 `.mjo`，将该行为与归档成员名逐一核对。记录动态参数的数据来源和可确认的候选。跨脚本函数哈希在多库出现时保留候选，直到查明加载状态及实际调用者。[MajiroTools MJO 结构](https://github.com/AtomCrafty/MajiroTools/wiki/Format:-Mjo-script) · [majiro-py 符号表](https://github.com/trigger-segfault/majiro-py/blob/f7ec450d5b78f0ed6df603b8c0b0ed79748d9cee/data/known_hashes_readable.json)

数值分派可读取紧跟菜单调用的 `switch` 或 `br.case`／`bne.case`。中间保存再读取选择结果时，应核对变量完整操作数和中间控制边界。备用 PC 登记和实际跳转分别记录。

匹配存档版本后，在真实槽位查找连续的脚本帧。把槽内 PC 当作代码相对坐标核对指令、脚本行和附近消息。使用另一个槽位检查前缀长度变化时帧仍能被发现，记录同位存档的覆盖限制。系统档和槽位头不同，槽位格式版本也可能随游戏变化。GalExtract 的 `scripts/locate_majiro_save.py` 支持已验证的 V1.105 连续帧。

<!-- EXPERIENCE:651aa3fb995be5c9f5229a57c747440d8be1ba172d1c26c917c4bc11c46119d0:START -->
## 绑定跨脚本字面量和菜单分派到原始指令位置

- 引擎版本：Majiro MJO V1 literal dispatch
- 方言/条件：Windows，限匹配脚本布局
- 阶段：reverse
- 验证等级：real_sample
- 经验 ID：`651aa3fb995be5c9f5229a57c747440d8be1ba172d1c26c917c4bc11c46119d0`

本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。

### 适用前提

- 提供严格解析过的脚本、文件名编码和明确的覆盖输入。

### 已验证步骤

- 用系统调用符号、原生基名规则及字节回读确认目标，分别核对数值分派、局部跳转和备用 PC。

### 限制与失效条件

- 动态参数、跨库加载、变量取值和运行路线需另验。

原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。
<!-- EXPERIENCE:651aa3fb995be5c9f5229a57c747440d8be1ba172d1c26c917c4bc11c46119d0:END -->
