# 游戏引擎验证记录

返回[引擎与代表游戏](../README.md#已验证的引擎与代表游戏)。验证项按实际样本记录，适用范围随发行版、补丁和格式变体变化。

## 引擎代表案例

| 状态 | 引擎 / 格式族 | 代表游戏 | 已验证范围 | 待验证项 |
| :---: | --- | --- | --- | --- |
| ✅ | SiglusEngine | Rewrite＋ | 场景解包、消息与显式姓名、局部分支；存档活动字段及部分静态坐标核对 | 全路线语义、动态调用与游戏内存档恢复 |
| ✅ | NScripter | 寒蝉鸣泣之时（ひぐらしのなく頃に） | 脚本解码、显示行候选、标签与字面量跳转目标 | 宏展开、动态姓名与存档恢复 |
| ✅ | Majiro | 片羽（カタハネ ―An' call Belle―） | ARC 解包、MJO V1 指令和局部分支、2 个真实 V1.105 槽位与剧情指令边界对照 | 部分补丁编码、完整消息拼接与读档恢复 |
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
| ✅ | [Liar-soft / RScript](../GalgameResourceExtract/engine/liar.md) | 漆黑的夏尔诺斯 Full Voice ReBORN | 标准 XFL 解包，原版 GSC 导出文本、姓名、选择和局部标签 | 非标准头汉化包、跨脚本控制流、存档和 CG 合成 |
| ✅ | [Leaf](../GalgameResourceExtract/engine/leaf.md) | WHITE ALBUM2 Special Contents | KCAP、LAC 归档解包与脚本载荷核对 | 脚本语义、封包和存档定位 |
| ✅ | [TyranoScript](../GalgameResourceExtract/engine/tyrano.md) | Teaching Feeling 4.0.6 | 已展开的 Electron 项目中定位并逐哈希校验 KS 场景副本 | 标签和宏执行、动态分支及存档 |
| ✅ | [MUSICA](../GalgameResourceExtract/engine/musica.md) | eden* | PAZ 逻辑成员、SC 台词及姓名、条件路线和嵌入脚本 | 两个小包的载荷、运行对照、实际槽位与封包 |
| ✅ | [Entis GLS / Cotopha](../GalgameResourceExtract/engine/entis-gls.md) | 狙われた女神天使エンゼルティアー FHD 版 | 大型 NOA、CSX 台词与姓名、真实槽位上下文解码 | 全部差分合成、完整运行分支、恢复和回封 |
| ✅ | [Bishop](../GalgameResourceExtract/engine/bishop.md) | 鬼父 after | BSArc v2 头下的固定名称索引、资源提取 | BSX 脚本和存档 |
| ✅ | [YU-RIS](../GalgameResourceExtract/engine/yuris.md) | MagusTale ～世界樹と恋する魔法使い～ | YPF 263 指定布局的名称、存储载荷校验及成员解包 | 其他 YPF 方言、YSTB 263 台词和封包 |
| ✅ | [KiriKiri](../GalgameResourceExtract/engine/kirikiri.md) | 千恋万花（千恋＊万花） | XP3 场景包解包，按序号保留同名成员并核对索引与载荷 | 场景语义、归档签名与游戏内加载 |

| ✅ | [CMVS](../GalgameResourceExtract/engine/cmvs.md) | 天津罪（アマツツミ） | CPZ6 与独立 PKP v0 补丁的索引及逻辑成员；同轮亦验证 CPZ3、CPZ5、CPZ7 | 脚本语义、PB3 图层与封包 |

《苍之彼方的四重奏》的 Unity 项目专用 DAT / BS5 路线已验证多语言台词与显式姓名提取，其他 Unity 项目的剧情或存档需另验。ShiinaRio 的既有样本仍有载荷读取障碍。

## 2026-11-12 新增安装目录

本轮依次核对 21 个安装目录。《白色相簿 2》本篇和两个附录分别计入。296 个候选中有 282 个通过，累计 440,865 个输出成员。另有 517 个场景 DAT。候选包含部分以归档扩展名存放的媒体，成员数含不同来源的补丁和同名成员。14 个候选仍待确认。

| 游戏或版本 | 引擎 | 实测结果 | 范围与待处理项 |
| --- | --- | --- | --- |
| 神采炼金大师 / 神採りアルケミーマイスター | Eushully AGE | 8/8 候选通过，20,126 个成员，散文件 667 | 按 S4IC 主索引和 S4AC 追加索引核对 ALF 成员。另核验 667 个散文件。 |
| 姬狩—魔王再临 / 姫狩りダンジョンマイスター | Eushully AGE | 6/6 候选通过，13,287 个成员，散文件 52 | 按外部索引切分 ALF 卷。另核验 52 个散文件。 |
| 甜蜜女友 3 / アマカノ3 | Artemis | 11/11 候选通过，50,634 个成员 | PF6 与 PF8 各卷独立核验，汉化 XP3 曾用旧版提取。Mod 默认读取失败，显式参数抽查通过。 |
| 望见青空之丘 / あおぞらの見える丘 | Yuka | 3/3 候选通过，12,225 个成员 | 独立核对 YKC001 索引和 YKS 文本区还原。 |
| 漆黑的夏尔诺斯 Full Voice ReBORN | Liar-soft / RScript | 19/20 候选通过，14,640 个成员 | 原版 183/183 GSC 导出 TSC 和文本，6,473 条带显式姓名的文本命令，5,900 个局部目标均可定位。汉化 XFL 跳过，存档待验证。 |
| BALDR SKY DiveX “DREAM WORLD” / 梦之世界 | NeXAS | 18/18 候选通过，36,623 个成员 | 补齐四个更新 PAC 的末条长度，按索引序号保留成员。 |
| eden* They were only two, on the planet. / 伊甸园 | MUSICA | 18/20 候选通过，15,258 个成员 | 逐组回读 36 条静态路径，覆盖 8 条嵌入引用和三套主线各 35 个条件点。原版进程已创建存档目录。真实槽位与两个小包的载荷仍待确认。 |
| MagusTale ～世界樹と恋する魔法使い～ / 世界树与恋爱的魔法使 | YU-RIS | 12/12 候选通过，19,044 个成员 | 逐条核验 YPF 263 的名称与存储载荷。脚本包含 244 个 YBN。 |
| Summer Pockets REFLECTION BLUE / 夏日口袋 | SiglusEngine | 517 个场景 DAT、3 个散文件 | 核对场景载荷连续至文件末尾，只修正读取副本中的源码尾部声明。 |
| Teaching Feeling 4.0.6 / 希尔薇 | TyranoScript / Electron | 37,943 项散文件，34 个 KS 副本 | Electron 应用的数据目录已展开，保留原相对路径核对 KS 场景副本。 |
| WHITE ALBUM2 / 白色相簿 2 本篇 | Leaf | 32/32 候选通过，43,128 个成员 | 分别核对 KCAP、LAC 以及以 PAK 为扩展名的 ASF 视频。 |
| WHITE ALBUM2 Special Contents / 白色相簿 2 特典 | Leaf | 13/13 候选通过，8,019 个成员 | 分别核对原脚本包与汉化脚本包。 |
| WHITE ALBUM2 ミニアフターストーリー / 白色相簿 2 迷你后日谈 | Leaf | 10/10 候选通过，1,546 个成员 | 分别核对独立后日谈的 KCAP 与 LAC。 |
| 五彩斑斓的世界 / いろとりどりのセカイ | Favorite View Point | 10/10 候选通过，22,780 个成员，散文件 1 | 分别核对 BIN 成员和散置 HCB。 |
| 千恋万花 / 千恋＊万花 | KiriKiri | 14/14 候选通过，48,418 个成员 | 场景包已解包，五个含同名条目的 XP3 按索引序号保存。 |
| 月姬 / 月姫 | NScripter | 1/1 候选通过，829 个成员，散文件 4 | 核对旧 PC 版 NSA 成员，并保留散置脚本。 |
| 琥珀结晶 / アンバークォーツ | Majiro | 11/11 实际归档通过，71,798 个成员 | 151 个汉化 MJO 对应更新包成员。按指定覆盖顺序核对 174 份脚本、160 条跨场景字面量引用、18 条库加载、57 处数值分派。随附全 CG 文件为系统状态。V1.103 槽位与动态路线待验证。 |
| 秽翼的尤斯蒂娅 / 穢翼のユースティア | BGI / Ethornell | 65/65 候选通过，44,286 个成员 | 本篇与补丁 ARC 各自核验。 |
| 花与乙女的祝福 / 花と乙女に祝福を | ShiinaRio | 7 个 WARC 1.7 可列索引，0 个包完成逻辑载荷验收 | 历史用两版 GARbro 对照原版与 Royal Bouquet 方案（现统一随附 Mod），小型脚本包均为 1/6 输出且脚本未获验证。载荷与两个 BIN 暂跳过。 |
| 赫炎的印加诺克 Full Voice ReBORN | Liar-soft / RScript | 25/26 候选通过，13,847 个成员 | 原版 412/412 GSC 导出 TSC 和文本，7,357 条带显式姓名的文本命令，6,907 个局部目标均可定位。汉化 XFL 跳过，存档待验证。 |
| 鬼父 after | Bishop | 6/6 候选通过，4,377 个成员，散文件 11 | 独立核对 BSArc v2 头下的定长索引和成员，另保留散置脚本候选。 |

本轮主要验证索引、解包和脚本载荷。完整剧情分支、说话人、存档定位、封包和游戏内加载各自验收。

格式、命令及适用边界见[引擎资料索引](../GalgameResourceExtract/catalog/engines.md)、[经验索引](../GalgameResourceExtract/catalog/experiences.json)和 [CG 实测状态表](../GalgameResourceExtract/catalog/cg-status.md)。

## 2026-11-12 紫社及其他新增安装样本

本轮逐一处理 13 个安装样本，包含《幸福噩梦》的另一个安装版本和《临界边界》前三部。在安装目录初筛的 125 个归档候选中，111 个通过逻辑成员解包校验，共 293,350 个成员。另有 137 个已核对的存储块，13 个归档候选待继续处理。成员数保留了各版本、补丁和同名条目的独立身份。

| 游戏或版本 | 引擎 / 格式 | 归档和逻辑成员 | 验证范围 |
| --- | --- | --- | --- |
| 天津罪 / アマツツミ | CMVS · CPZ6 / PKP v0 | 18/18，30,869 个成员 | 四个 PKP v0 补丁共 729 个成员，逐条检查裸 DEFLATE 的结束与输出长度。原版与补丁分开保存。 |
| 幸福噩梦 / ハピメア（另一个安装版本） | CMVS · CPZ5 | 13/13，25,641 个成员 | 补丁归档与此前登记的安装版本不同。 |
| 幸福噩梦 Fragmentation Dream / ハピメア Fragmentation Dream | CMVS · CPZ5 | 12/12，22,746 个成员 | 原版与补丁分开保存。 |
| 日在盛夏 / Summer Days | rUGP · MSI/CAB / RIO | 原版跨卷 CAB 交付 127/127 个 MSI 安装文件 | 原版与 1.09B 均确认内嵌 RIO 根对象头，读取器均报 `Bad class`。旧式 Cr6Ti 和 OOR 复扫均无候选，内部目录和 CG 暂跳过。 |
| 临界边界 1 / Liminal Border Part I / クリミナルボーダー 1st Offence | KiriKiri · XP3 | 7/7，9,442 个成员 | 历史由旧版提取媒体，两个含脚本的包按标准段读取。Mod 显式参数复验了语音包和主数据包的抽样成员，发现一个 MDF 输出层级差异。 |
| 临界边界 2 / Liminal Border Part II / クリミナルボーダー 2nd Offence | KiriKiri · XP3 | 0/6，0 个成员 | 确认 Hxv4 顶层索引及配套程序资源结构；归档载荷仍待验证。待处理 `data.xp3`、`voice.xp3`、`bgimage.xp3`、`video.xp3`、`fgimage.xp3`、`evimage.xp3`。对应索引列出 8,480 项。 |
| 临界边界 3 / Liminal Border Part III / クリミナルボーダー 3rd Offence | KiriKiri · XP3 | 0/6，0 个成员 | 确认 Hxv4 顶层索引及配套程序资源结构；归档载荷仍待验证。待处理 `data.xp3`、`voice.xp3`、`video.xp3`、`bgimage.xp3`、`fgimage.xp3`、`evimage.xp3`。对应索引列出 7,962 项。 |
| 为与明日君相逢 / 明日の君と逢うために | CMVS · CPZ3 | 9/9，27,414 个成员 | 核对旧版 CPZ3 与脚本成员。 |
| 久那土国记 / Kunado Chronicles / クナド国記 | KiriKiri · XP3 | 5/5，33,891 个成员 | 两个目录的 5 个 XP3 逐包 SHA-256 相同，只计一组。历史采用 GARbro 1.5.44 提取。Mod 显式参数下主数据包抽查一致，带非零过滤标志的小补丁仍待处理。 |
| 未来乡愁 / 未来ノスタルジア | CMVS · CPZ5 | 9/9，35,299 个成员 | CPZ 全部通过，散置 mirai.bin 的编码仍待确认。 |
| 柯罗的怀表 / ChronoClock / クロノクロック | CMVS · CPZ6 | 13/13，25,864 个成员 | 核对脚本、附加语音、更新包与原生图像。 |
| 重生游戏 / リアライブ | CMVS · CPZ7 | 12/12，42,706 个成员 | 由原始 CPZ7 文件头与实际成员确认引擎。 |
| 青鸟 / Aoi Tori / アオイトリ | CMVS · CPZ7 / Longinus | 13/14，39,478 个成员 | Longinus 独立覆盖包保留 137 个已哈希的存储块，内部语义待确认。背景包改用 Akaibu CLI 0.1.17，128 个 PB3 成员通过索引、长度与文件头核验。 |

解包输出保留原生脚本、图像和其他资源的字节及来源。对白语义、说话人、分支、存档位置、CG 差分合成、封包及游戏内加载分别验收。

《临界边界》三部与《久那土国记》的发行名见 [Shiravune 的 Liminal Border 系列](https://store.steampowered.com/bundle/39287/Liminal_Border_Bundle/)、[Kunado Chronicles 发行页](https://shiravune.com/archives/3751) 和 [Purple Software 原作页](https://www.purplesoftware.jp/products/newproject/index.html)。《柯罗的怀表》的英文名见 [Sekai Project 发行页](https://sekaiproject.com/zh-hant/product/chronoclock/?v=84de8e2b14bb)。

## 2026-11-12 Muv-Luv Alternative

| 阶段 | Steam alternative16 | 原版 alternative14 | 验证范围 |
| --- | --- | --- | --- |
| ICI/RIO 目录 | 3 卷，1,939 个对象 | 3 卷，343 个对象 | 两版的卷名、声明尺寸和目录对象范围全部核对。 |
| CRsa 脚本载荷 | 510 个（目录 72 个） | 176 个（目录 26 个） | 按物理来源保留原始 CRsa 和解密 VM 载荷。目录条目已包含在物理扫描数中，RUO 单独保留。 |
| OOR 音频 | 26,148 条，附 829 份元数据 | 25,935 条 | 按卷内范围逐条比对字节，另有 21 条通过 WAV 抽检。 |
| 图像 | 6,650 个原生候选，1,813 个 PNG | 现有扫描无通过候选 | Steam 版完成全量候选原样核验，PNG 为有界批次及跨卷分层抽样，其中 316 个有部分透明像素。 |
| RUO | 268 个重定向载荷 | 本样本未见 RUO | 按现存顺序保留目标范围和原始字节，未生成新补丁。 |

对白候选保留脚本、字段偏移及分类，完整台词、说话人、分支、存档位置与语音引用待验证。CG 组合、原版图像方言、非 RIO 附件和游戏内加载也待验证。 [Steam 发行页](https://store.steampowered.com/app/802890/MuvLuv_Alternative/)

## 2026-11-12 Muv-Luv Alternative 图像与 CRsa 续处理

| 阶段 | 本轮结果 | 验证边界 |
| --- | --- | --- |
| 原版图像 | 2,457 个 Cr6Ti，121 个有部分透明像素，220 个带绘制偏移 | 保留原生字节、RGBA 与 PNG 读回结果，另有 18 个独立像素复核。30 个其他编码候选仍未确认，CG 父子层组合待验证。 |
| Steam 图像 | 6,650 个已核验，本轮新增 4,837 个 | 覆盖此前登记的全部原生候选，含一条校正精确范围及零填充位的 CRip007。 |
| Steam CRsa v18 | 255/255 个生效脚本完整顺序读取，54,553 条带位置的消息 | 核对 RUO 到基础脚本身份，按三语言槽合并。40,002 条有日语槽显式说话人前缀。 |
| 原版 CRsa v17 | 176 个脚本中 53 个读到声明命令流末尾；28,948 条消息 | 18,895 条来自完整命令流，其余来自确认的顺序前缀。21,541 条有显式说话人。 |
| Steam 静态分支 | 223,642 个指令坐标，228 个选择相关操作 | 12,966 个条件目标命中唯一同脚本坐标。122 个标签跳转已配对，1 个待确认。另保留跨脚本资源引用。 |
| 存档定位 | 4 个 Steam 读写存档指令位置 | 已有静态指令坐标，未找到与两版对应的存档样本，当前恢复位置和分支状态待验证。 |

## 2026-11-12 狙われた女神天使エンゼルティアー FHD 版

| 阶段 | 结果 | 验证边界 |
| --- | --- | --- |
| NOA 解包 | 主游戏和附赠短篇的 23 个顶层包共 70,650 个成员。另解包 7 个内嵌 NOA，共 1,198 个成员 | 顶层清单与 GARbro 对照并核对输出哈希，2,646 个成员起点超出 4 GiB。附赠短篇的 ERISA 脚本独立解码。 |
| 图像 | 18 个 ERI 样本全部导出 PNG，含两个超 4 GiB 包的尾部样本 | 原生资源全部保留，完整 CG 和差分合成待验。 |
| CSX | 主游戏 71,298 次对白调用，附赠短篇 5,166 次 | 核对姓名、正文、语音参数和指令位置。主游戏 38,705 次含显式姓名，2,470 个字面跳转命中反汇编边界，10 个待确认。 |
| Cotomi 槽位 | 79 份文件去重后得到 48 个上下文，全部解码。21 个预览文本唯一对应当前脚本的一处对白 | 46 个首字段与保存函数的后继指令吻合，另外 2 个未匹配当前指令边界。完整剧情调用栈和游戏内恢复待验。 |

本地主脚本与所附汉化脚本哈希一致。附赠短篇、原生图片、台词和存档证据在工作区独立保存。 [SYRUP 官方版本说明](https://syrup-soft.com/mm/megami/)

## 2026-11-13 CG 按包抽样

本轮新增 37 个安装样本的 CG 抽样记录，按现有索引与媒体特征选中 438 个候选包、包内资源组或散文件组，其中 414 个有可读样本，2 款的选中范围完全受阻。同一原始包可按用途计为多个资源组。统计涵盖候选图、配套蒙版、立绘、背景和子图，完整 CG 库及实际叠层另验。

详见 [CG 实测状态表](../GalgameResourceExtract/catalog/cg-status.md#2026-11-13-cg-按包抽样)。

## 2026-11-13 GARbro Mod 迁移抽查

串行复测了 16 款游戏的 18 个代表包。8 个包可用默认 CLI 抽查提取，另有 4 个包使用 Mod 读取库的显式选项后通过抽查。一个 XP3 的样本包含需分层比较的 MDF，另一个 WARC 只读出部分成员，4 个包仍待处理。表中列出每个包的历史基线、索引与字节对照，以及封包限制。 [GARbro Mod 迁移抽查表](garbro-mod-retest.md)
