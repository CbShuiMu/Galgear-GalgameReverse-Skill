# 游戏引擎验证记录

返回[引擎与代表游戏](../README.md#已验证的引擎与代表游戏)。验证项按实际样本记录，适用范围随发行版、补丁和格式变体变化。

## 引擎代表案例

| 状态 | 引擎 / 格式族 | 代表游戏 | 已验证范围 | 待验证项 |
| :---: | --- | --- | --- | --- |
| ✅ | SiglusEngine | Rewrite＋ | 场景解包、消息与显式姓名、局部分支；存档活动字段及部分静态坐标核对 | 全路线语义、动态调用与游戏内存档恢复 |
| ✅ | NScripter | 寒蝉鸣泣之时（ひぐらしのなく頃に） | 脚本解码、显示行候选、标签与字面量跳转目标 | 宏展开、动态姓名与存档恢复 |
| ✅ | Majiro | 片羽（カタハネ ―An' call Belle―） | ARC 解包、匹配 MJO V1 的指令遍历、Text 片段与内联姓名、局部分支 | 部分补丁编码、完整消息拼接与存档格式 |
| ✅ | Artemis | 常轨脱离 Creative（ハミダシクリエイティブ） | AST 文本、姓名、多语言选项与显式选择标签 | 宏执行、跨场景运行顺序与存档活动 PC |
| ✅ | RealLive | 智代 After ～It’s a Wonderful Life～ | SEEN 拆分与解压、消息及姓名、指令与字符串坐标、局部跳转 | 部分脚本、选择模块与存档读取 |
| ✅ | BGI / Ethornell | 美好的每一天 ～不连续存在～ Full Voice HD | 脚本子集解包、消息及姓名消费者、原始字符串引用核对 | 失败脚本、完整分支图与存档活动字段 |
| ✅ | Ren’Py | 片轮少女（かたわ少女） | RPA 解包、RPYC 反编译、静态台词与姓名表、菜单和标签调用图 | 动态 Python、返回栈与存档定位 |
| ✅ | System-NNN | 虫爱少女 | SPT 消息、姓名、选项、直接跳转、子程序与脚本名表 | 完整条件求值、旧版存档布局与加载验证 |
| ✅ | Nitroplus 格式族 | 沙耶之歌（沙耶の唄） | PAK 脚本子集提取、翻页文本候选、显式姓名及标签引用 | 混合编码乱码、其他容器变体与完整剧情语义 |
| ✅ | NeXAS | 认真和我恋爱！（真剣で私に恋しなさい!!） | PAC 脚本子集解包与成员核验 | BIN 台词、姓名、分支及存档语义 |
| ✅ | FVP | 星空的记忆 -Wish upon a shooting star- | 匹配 HCB 布局的指令遍历与字符串候选提取 | 汉化布局变体、对白分类、姓名及存档定位 |
| ✅ | rUGP | Muv-Luv | 标准 Cr6Ti／CRip008 图像载荷、透明差分与绘制矩形；Cr6Ti 和累计 RUO 的静态往返 | CBg2d、完整 CG 组合、完整 RIO 重建和游戏内加载 |
| ✅ | [Eushully AGE](../GalgameResourceExtract/engine/eushully.md) | 神采炼金大师（神採りアルケミーマイスター） | 按主索引和 AAI 识别并提取 ALF 逻辑成员 | AGF 转换、脚本和加载 |
| ✅ | [Yuka](../GalgameResourceExtract/engine/yuka.md) | 望见青空之丘（あおぞらの見える丘） | YKC001 解包及 YKS 文本区还原抽检 | YKS 指令、分支和存档 |
| ✅ | [Liar-soft / RScript](../GalgameResourceExtract/engine/liar.md) | 漆黑的夏尔诺斯 Full Voice ReBORN | 标准 XFL 解包与 GSC 载荷保留 | 非标准头汉化包、GSC 语义和 CG 合成 |
| ✅ | [Leaf](../GalgameResourceExtract/engine/leaf.md) | WHITE ALBUM2 Special Contents | KCAP、LAC 归档解包与脚本载荷核对 | 脚本语义、封包和存档定位 |
| ✅ | [TyranoScript](../GalgameResourceExtract/engine/tyrano.md) | Teaching Feeling 4.0.6 | 已展开的 Electron 项目中定位并逐哈希校验 KS 场景副本 | 标签和宏执行、动态分支及存档 |
| ✅ | [MUSICA](../GalgameResourceExtract/engine/musica.md) | eden* | 显式方案选择，原版和附加脚本包逻辑成员校验 | 部分同版本或改名归档、脚本语义和封包 |
| ✅ | [Bishop](../GalgameResourceExtract/engine/bishop.md) | 鬼父 after | BSArc v2 头下的固定名称索引、资源提取 | BSX 脚本和存档 |
| ✅ | [YU-RIS](../GalgameResourceExtract/engine/yuris.md) | MagusTale ～世界樹と恋する魔法使い～ | YPF 263 指定布局的名称、存储载荷校验及成员解包 | 其他 YPF 方言、YSTB 263 台词和封包 |
| ✅ | [KiriKiri](../GalgameResourceExtract/engine/kirikiri.md) | 千恋万花（千恋＊万花） | XP3 场景包解包，按序号保留同名成员并核对索引与载荷 | 场景语义、归档签名与游戏内加载 |

《苍之彼方的四重奏》的 Unity 项目专用 DAT / BS5 路线已验证多语言台词与显式姓名提取，其他 Unity 项目的剧情或存档需另验。CMVS 的既有样本和 ShiinaRio 的本轮样本仍有载荷读取障碍。

## 2026-11-12 新增安装目录

本轮依次核对 21 个安装目录。《白色相簿 2》本篇和两个附录分别计入。296 个候选中有 282 个通过，累计 440,865 个输出成员。另有 517 个场景 DAT。候选包含部分以归档扩展名存放的媒体，成员数含不同来源的补丁和同名成员。14 个候选仍待确认。

| 游戏或版本 | 引擎 | 实测结果 | 范围与待处理项 |
| --- | --- | --- | --- |
| 神采炼金大师 / 神採りアルケミーマイスター | Eushully AGE | 8/8 候选通过，20,126 个成员，散文件 667 | 按 S4IC 主索引和 S4AC 追加索引核对 ALF 成员。另核验 667 个散文件。 |
| 姬狩—魔王再临 / 姫狩りダンジョンマイスター | Eushully AGE | 6/6 候选通过，13,287 个成员，散文件 52 | 按外部索引切分 ALF 卷。另核验 52 个散文件。 |
| 甜蜜女友 3 / アマカノ3 | Artemis | 11/11 候选通过，50,634 个成员 | PF6 与 PF8 各卷独立核验，汉化 XP3 使用兼容后端。 |
| 望见青空之丘 / あおぞらの見える丘 | Yuka | 3/3 候选通过，12,225 个成员 | 独立核对 YKC001 索引和 YKS 文本区还原。 |
| 漆黑的夏尔诺斯 Full Voice ReBORN | Liar-soft / RScript | 19/20 候选通过，14,640 个成员 | 标准 XFL 已解包，非标准头的汉化补丁包仍待识别。 |
| BALDR SKY DiveX “DREAM WORLD” / 梦之世界 | NeXAS | 18/18 候选通过，36,623 个成员 | 补齐四个更新 PAC 的末条长度，按索引序号保留成员。 |
| eden* They were only two, on the planet. / 伊甸园 | MUSICA | 18/20 候选通过，15,258 个成员 | 分别核对原版、PLUS+MOSAIC 和汉化 PAZ。两个小包待确认。 |
| MagusTale ～世界樹と恋する魔法使い～ / 世界树与恋爱的魔法使 | YU-RIS | 12/12 候选通过，19,044 个成员 | 逐条核验 YPF 263 的名称与存储载荷。脚本包含 244 个 YBN。 |
| Summer Pockets REFLECTION BLUE / 夏日口袋 | SiglusEngine | 517 个场景 DAT、3 个散文件 | 核对场景载荷连续至文件末尾，只修正读取副本中的源码尾部声明。 |
| Teaching Feeling 4.0.6 / 希尔薇 | TyranoScript / Electron | 37,943 项散文件，34 个 KS 副本 | Electron 应用的数据目录已展开，保留原相对路径核对 KS 场景副本。 |
| WHITE ALBUM2 / 白色相簿 2 本篇 | Leaf | 32/32 候选通过，43,128 个成员 | 分别核对 KCAP、LAC 以及以 PAK 为扩展名的 ASF 视频。 |
| WHITE ALBUM2 Special Contents / 白色相簿 2 特典 | Leaf | 13/13 候选通过，8,019 个成员 | 分别核对原脚本包与汉化脚本包。 |
| WHITE ALBUM2 ミニアフターストーリー / 白色相簿 2 迷你后日谈 | Leaf | 10/10 候选通过，1,546 个成员 | 分别核对独立后日谈的 KCAP 与 LAC。 |
| 五彩斑斓的世界 / いろとりどりのセカイ | Favorite View Point | 10/10 候选通过，22,780 个成员，散文件 1 | 分别核对 BIN 成员和散置 HCB。 |
| 千恋万花 / 千恋＊万花 | KiriKiri | 14/14 候选通过，48,418 个成员 | 场景包已解包，五个含同名条目的 XP3 按索引序号保存。 |
| 月姬 / 月姫 | NScripter | 1/1 候选通过，829 个成员，散文件 4 | 核对旧 PC 版 NSA 成员，并保留散置脚本。 |
| 琥珀结晶 / アンバークォーツ | Majiro | 11/12 候选通过，71,798 个成员，散文件 151 | 核对 Majiro V2 ARC 及散置 MJO，另有一个补丁候选待确认。 |
| 秽翼的尤斯蒂娅 / 穢翼のユースティア | BGI / Ethornell | 65/65 候选通过，44,286 个成员 | 本篇与补丁 ARC 各自核验。 |
| 花与乙女的祝福 / 花と乙女に祝福を | ShiinaRio | 0/9 候选通过，0 个成员，散文件 2 | 七个 WARC 1.7 能列出索引，逻辑载荷仍受阻。另有两个 BIN 待识别。 |
| 赫炎的印加诺克 Full Voice ReBORN | Liar-soft / RScript | 25/26 候选通过，13,847 个成员 | 标准 XFL 已解包，非标准头的汉化补丁包仍待识别。 |
| 鬼父 after | Bishop | 6/6 候选通过，4,377 个成员，散文件 11 | 独立核对 BSArc v2 头下的定长索引和成员，另保留散置脚本候选。 |

本轮主要验证索引、解包和脚本载荷。完整剧情分支、说话人、存档定位、封包和游戏内加载各自验收。

格式、命令及适用边界见[引擎资料索引](../GalgameResourceExtract/catalog/engines.md)、[经验索引](../GalgameResourceExtract/catalog/experiences.json)和 [CG 实测状态表](../GalgameResourceExtract/catalog/cg-status.md)。
