# CriCodecs CLI：AI 助手调用参考

## 适用范围与版本

- 入口：相对于本技能目录的 `tools/cricodecs/cricodecs.exe`。调用方从技能根目录解析实际工具路径，保存为 `$cri`；不要依赖当前工作目录或写死开发机路径。
- 已核对版本：`1.2.0 (rev 970f3feaf49e)`，2026-10-18。
- 二进制 SHA-256：`610A2A133649A25771012BD98F25EF77661ECB50CA4F249C43DEF44704A437B9`。
- 用途：CRI 容器列表/提取/创建/修改，HCA/ADX/AHX 音频编解码，以及支持格式的加解密和密钥候选恢复。
- 不解析 MAGES SC3 `.scx` 对白、中文字体码表、游戏脚本语音调用或对白映射。CPK 中取出 `.scx` 后交给脚本工具；HCA 编码成功不等于游戏可播放。
- 这是独立原生 CLI，不使用旧 `PyCriCodecs` 的 Python API，也不使用 GARbro 的 `x/l/c` 子命令。工具更新后先执行 `--version` 和 `--help`，再复核受影响参数。

按任务读取：解包见“列表与输出路径”；CPK 写回见“CPK”；配音转换见“HCA”；ACB 对白音频定位见“ACB”；其他容器见“其他创建模式”。

## 调用约定

```powershell
& $cri --version
& $cri --help
# $cri、$inputFile、$outputFile 等变量由调用方赋为已解析的路径。
& $cri $inputFile -m --json
if ($LASTEXITCODE -ne 0) { throw 'CriCodecs metadata failed' }
```

- 普通操作每次恰好一个输入路径；仅 `--recover-key` 接受多个输入或目录。批处理由调用方枚举文件，逐次检查退出码；CLI 不展开通配符。
- 选项和值分为两个参数，如 `--quality high`。不要使用 `--quality=high`。布尔开关不附带 `true/false`。
- 文件系统路径含空格时保持为一个参数。`LEFT=RIGHT` 必须作为一个完整参数传入，例如 `--replace "${entryIndex}=$replacementFile"`；不要把拼接结果交给 `Invoke-Expression`。
- 普通数值接受十进制或 `0x` 十六进制；**修改命令的条目索引使用十进制**。文件名、索引、CPK ID、AWB wave ID、ACB cue ID 不能互换。
- 写操作没有通用的“不覆盖/重命名/跳过/试运行”开关。使用不同于源文件的新输出路径，调用前检查输出是否已存在。不要添加 GARbro 的 `-y`、`-s`、`-r` 或 `-R`。
- 创建输出放在输入目录外；目录构建会递归收集全部普通文件，不提供排除模式，也不会自动忽略目录内旧输出、清单或日志。
- 成功通常返回 `0`；解析、读取、操作失败返回 `1`。无参数只显示帮助且返回 `0`，不能据此认定已处理资源。
- stdout：元数据/列表/密钥恢复结果；写操作默认输出 `build/format/output/done` 等文本。stderr：错误。`-q` 抑制普通进度，不抑制 JSON 结果或错误。
- `--json` 仅与 `-m`、`--list`、`--recover-key` 使用；不提供编码/构建/提取的 JSON 结果。解析 JSON 时分开收集 stderr，不能用 `2>&1` 混入 JSON。

## 操作选择

| 目标 | 参数形态 |
| --- | --- |
| 检测格式与查看元数据 | `INPUT -m --json` |
| 列出可导出条目 | `INPUT --list --json` |
| 提取容器、音频默认解码为 WAV | `INPUT -o OUTPUT`；`-e` / `--export` 与默认操作相同 |
| 提取编码资源，避免音频解码 | `INPUT --raw -o OUTPUT` |
| WAV 编码 | `--encode -f hca\|adx\|ahx INPUT.wav -o OUTPUT` |
| 创建容器 | `--build -f TYPE INPUT -o OUTPUT` |
| 修改已有容器 | `INPUT --replace INDEX=LOCAL_FILE -o OUTPUT` 等 |
| 对已有文件加解密 | `INPUT --encrypt\|--decrypt -o OUTPUT`，其他参数依格式提供 |
| 密钥候选恢复 | `--recover-key -f TYPE INPUT [INPUT ...] --json` |

`-f` / `--force-type` 强制格式解析；编码/构建时选择目标格式，恢复时选择恢复域。主要有效值：`aax acb acx adx afs ahx aix awb cpk csb cvm hca sfd usm utf`。识别能力不等于创建、编辑或加解密能力；UTF 默认仅显示元数据，不能通过 CLI 导出或重建表。

互斥规则：

- `-m` 不与列表、提取筛选、加解密或 `-o` 混用。
- `--list` 不与 `-o`、`-m`、加解密混用；`--verbose` 仅用于列表。
- `--encode` / `--build` 必须提供 `-f`、`-o`，不能与 JSON、列表、元数据、`--raw`、`--index`、`--encrypt/--decrypt` 混用。
- 修改命令必须提供 `-o`，不能与编码、构建、JSON、列表、元数据、`--raw`、`--index`、加解密混用。
- `--encrypt` 与 `--decrypt` 互斥，且不能与 `--raw` 或 `--index` 混用。
- `--compress` 只用于 CPK 构建或 CPK 新增/替换；它不是通用压缩命令。

## 列表与输出路径

```powershell
& $cri $archive -m --json
$listText = & $cri $archive --list --raw --json
if ($LASTEXITCODE -ne 0) { throw 'CriCodecs listing failed' }
$listing = ($listText -join "`n") | ConvertFrom-Json
& $cri $archive --list --raw --verbose --index $entryIndex --json
```

列表 JSON 基本结构：

```json
{"format":"cpk","mode":"entries","raw":true,"item_count":2,"items":[{"index":0,"name":"a.bin","path":"a.bin"},{"index":1,"name":"b.txt","path":"sub/b.txt"}]}
```

- `items[].index` 是本次列表的零基索引；CPK 写回以此为准。`name` 可能只有基本文件名，按 `path` 匹配完整资源路径。
- `--verbose` 或指定 `--index` 可为部分格式增加细节；CPK 列表不保证提供每条目的 ID、大小、压缩状态等字段。不要虚构不存在的 JSON 字段。
- `--index N` 可重复，用于导出或筛选列表。不要用它替代修改命令的目标参数。单个 HCA/ADX 的普通解码不使用 `--index`。
- 默认输出：独立 HCA/ADX/AHX/AAX 解码到源文件旁的同名 `.wav`；多条目容器输出到源文件旁的同名无扩展名目录。自动推导可能与已有文件冲突，自动化优先显式传 `-o`。
- **多条目操作最终只选中一个条目时，`-o` 被解释为完整输出文件路径，哪怕该路径看起来像目录。** 多于一个条目时，`-o` 是输出根目录，再附加条目相对路径。此规则也影响只有一个文件的归档。
- 要统一保留目录结构，先列出原样条目，再逐条导出到 `Join-Path $extractRoot $entry.path`；每次传该条目的 `--index`。不要假定 `--index N -o DIR` 会自动附加原文件名。
- `-o` 支持占位符：`?i` = 未补零的列表索引，`?e` = 条目基本文件名（含扩展名），`?s` = 输入文件基本名（不含扩展名）。占位符构成完整路径，不会自动附加条目目录。`?e` 单独使用可能因不同目录同名文件而覆盖。

```powershell
# 已确认 index 对应目标路径；$singleOutput 是完整文件路径。
& $cri $archive --raw --index $entryIndex -o $singleOutput
# 明确采用索引命名；此例扁平化目录，不能用于需要保留资源路径的重建。
& $cri $archive --raw -o (Join-Path $extractRoot '?i_?e')
```

CPK 提取会解开 CRILAYLA，导出归档内资源自身的编码字节；归档内 `.hca` 不会被递归转为 WAV。对 AWB/ACB 等音频容器，默认导出可能解码，制作重建基线时使用 `--raw`。独立 HCA/ADX 的 `--raw` 可能重建文件头，不用它代替文件复制来保证整文件哈希不变。

## CPK：创建、替换与验证

### 检查与创建

```powershell
& $cri $originalCpk -m --json
& $cri $originalCpk --raw --list --json
& $cri --build -f cpk $stagingDir -o $newCpk --profile filename-id --alignment 2048
# 确认需要压缩时才增加 --compress。
```

`--profile` 是字符串预设，**不是 `--mode 0/1/2/3`**。该版本 CPK 创建默认 `filename`、对齐 `2048` 字节，不能据此推断原始归档配置。可选预设及默认表组合：

| profile | TOC | ITOC | GTOC | ETOC |
| --- | --- | --- | --- | --- |
| `id` | 无 | 有 | 无 | 无 |
| `filename` | 有 | 无 | 无 | 有 |
| `filename-id` | 有 | 有 | 无 | 有 |
| `filename-group` | 有 | 无 | 有 | 有 |
| `id-group` | 有 | 有 | 有 | 无 |
| `filename-id-group` | 有 | 有 | 有 | 有 |

- `-m --json` 提供 `alignment/content_offset/utf_version/has_toc/has_itoc/has_gtoc/has_etoc` 等；自定义原始归档组合可能无法用上述预设精确表达。
- 创建会递归收集文件，按相对路径排序，归档内路径相对于输入目录根；无 `-R`，无尾部斜杠特殊语义。
- `--alignment` 非零，CPK 上限 `65535`；实际值按原始归档取。`--encoding NAME` 是容器文本字段编码覆盖，不是 SC3 对白或音频编码转换。
- CLI 不提供逐文件指定 CPK ID、组信息、时间、CRC、TVERSION 等全部底层构建选项。不要声称目录重建自动保留原始归档 ID、条目顺序或全部元数据。
- 少量文件替换优先读取原始归档后 mutation，再核对元数据和资源；mutation 也不保证输出与原始归档逐字节一致。

### 修改已有 CPK

```powershell
# $entryIndex 从原包的 --list --raw --json 按完整 path 唯一匹配获得。
& $cri $originalCpk --replace "${entryIndex}=$replacementFile" -o $newCpk
# 多个替换：重复 --replace；只替换时索引来自同一原包。
& $cri $originalCpk --replace "${firstIndex}=$firstFile" --replace "${secondIndex}=$secondFile" -o $newCpk
& $cri $originalCpk --add "$localFile=$archivePath" -o $newCpk
& $cri $originalCpk --rename "${entryIndex}=$newArchivePath" -o $newCpk
& $cri $originalCpk --remove $entryIndex -o $newCpk
& $cri $originalCpk --move "${fromIndex}=$toIndex" -o $newCpk
```

- **CPK 的 `--replace`、`--remove`、`--rename` 只接受十进制条目索引，不接受文件名/资源路径。** `--replace "voice/a.hca=local.hca"` 在此版本报 `CPK --replace target must be an entry index`。不要照搬上游新版或其他工具的按路径示例。
- `--add` 为 `本地文件=包内路径`，`--replace` 为 `索引=本地文件`；两者方向不同。
- mutation 按命令行顺序执行；新增、删除、移动可能改变后续索引。需要组合结构修改时分阶段保存并重新列出索引，不能重复使用旧索引。
- 保存可能重新排序 TOC；`--move` 成功不保证下一次列表顺序按请求变化。游戏按 ID/物理顺序取资源时，还需相应身份验证。
- `--compress` 请求压缩本次新增/替换的 CPK payload；不代表压缩所有未修改条目。
- `--encrypt/--decrypt` 对 CPK 处理 UTF 索引表混淆，和 HCA 音频加密不同；不能与 mutation/build 同一命令使用。需要时对新包另行处理：

```powershell
& $cri $newCpk --encrypt -o $encryptedCpk
& $cri $encryptedCpk --decrypt -o $plainCpk
```

创建/修改后重新读取元数据及原样列表；在新的验证目录原样提取，比较完整路径、数量以及替换/未修改条目的哈希。CPK 列表索引与 CPK ID 区分记录。输出包放在源游戏外完成验证；不能用“可解包”替代游戏内加载/播放验证。

## HCA：元数据、解码、编码与加密

```powershell
& $cri $originalHca -m --json
& $cri $originalHca -o $decodedWav
# 加密输入：仅在已确认密钥/子密钥后提供。
& $cri $originalHca --key $hcaKey --subkey $subkey -o $decodedWav
# WAV 必须已具备目标采样率、声道与所需循环元数据。
& $cri --encode -f hca $replacementWav -o $newHca --header-version 2.00 --quality high
# 编码后同时加密：使用 key/cipher 参数，不要附加 --encrypt。
& $cri --encode -f hca $replacementWav -o $newHca --header-version 2.00 --cipher-type 56 --key $hcaKey --subkey $subkey
# 对已有 HCA 单独加解密。
& $cri $plainHca --encrypt --cipher-type 56 --key $hcaKey --subkey $subkey -o $encryptedHca
& $cri $encryptedHca --decrypt --key $hcaKey --subkey $subkey -o $plainHcaOutput
```

| 参数 | 语义 |
| --- | --- |
| `--header-version` | `1.02`、`1.03`、`2.00`、`3.00`；默认 `2.00`。使用源游戏可接受的版本 |
| `--quality` | `highest/high/middle/low/lowest`；`medium` 是 `middle` 别名；默认 `high` |
| `--bitrate BPS` | 显式比特率；`0` 自动选择；单位 bit/s，不是 kb/s |
| `--ms-stereo` | 开启 mid/side 立体声编码；不用于单声道 |
| `--key` | 无符号十进制或 `0x` 十六进制 keycode；字符串形式传递以免 JSON/浮点数截断 64 位整数 |
| `--subkey` | `0..65535`；按原始音频/声库证据提供 |
| `--cipher-type` | 加密类型 `1` 或 `56`；type 56 需要有效 key/subkey |

- CLI 无采样率、声道、采样格式转换参数；编码采用输入 WAV 的采样率与声道。需要转换时先使用现有音频工具生成目标 WAV，再编码。
- `--encode -f hca` 未指定 key/cipher/subkey 时输出未加密 HCA；提供 key、cipher 或非零 subkey 会触发加密，默认 type 56。**不要用 `--cipher-type 0` 表示无加密。**
- 对已有 HCA 使用 `--encrypt` 时，未给 key/subkey 默认 type 1；给了 key 或非零 subkey 默认 type 56。自动化显式指定已确认类型。
- 编码读取 WAV `smpl` 的首个有效循环；该版本独立 HCA→WAV 导出未转写 HCA 循环信息。循环资源往返时另存并恢复循环元数据；对白不应意外带入循环。
- `-m --json` 可检查 `version/version_raw/channels/sample_rate/sample_count/frame_count/frame_size/encoder_delay/encoder_padding/encrypted/cipher_type/loop_count`。采样帧、声道数、压缩字节、解码 PCM 字节分别处理。
- HCA 有损编码后不要要求解码 WAV 与编码前 WAV 哈希一致；检查解码成功、采样率、声道、有效采样数、循环和试听。加解密前后可比较解码 PCM；保留原 WAV 和原 HCA。

## ADX / AHX 编码

```powershell
& $cri --encode -f adx $inputWav -o $outputAdx --mode 3 --header-version 4 --highpass 500
& $cri --encode -f ahx $inputWav -o $outputAhx --mode 0x10 --profile 48000
& $cri $outputAhx -f ahx -m --json
& $cri $outputAhx -f ahx -o $verifyWav
```

- ADX：`--mode 2/3/4`，默认 `3`；`--header-version 3/4/5`；`--highpass HZ`；`--trim-after-loop` 删除最终循环结束后的采样，不能无条件用于对白。
- AHX：`--mode 0x10/0x11`，默认 `0x10`；`--profile default/22050/24000/44100/48000` 是位分配预设，**不是重采样参数**。
- 编码加密只有提供 `--key` 才启用，`--cipher-type` 为 `8/9`，默认 `8`。type 8 使用格式所需 key string；type 9 使用 numeric keycode，可带 `--subkey`。AHX 也支持 `start,mult,add` 三元组；此 CLI 的 ADX 编码不接受三元组。
- 原有 ADX 单独 `--encrypt` 与编码默认值不同：未显式给 cipher 时数值 key 可选择 type 9。避免隐式推断，明确指定已确认类型。
- 实测生成的 48 kHz AHX 可编码/强制解析/解码，但自动探测报 `could not detect supported format`；已确认 AHX 时使用 `-f ahx`，不能只凭自动探测失败判断文件损坏。

## ACB / AWB：波形与 cue

```powershell
& $cri $soundBank --raw --list --json
& $cri $soundBank --raw --index $waveIndex -o $rawAudioFile
& $cri $soundBank --index $waveIndex --key $hcaKey -o $decodedWav
& $cri $acb --cue --list --json
& $cri $acb --cue --list --index $planIndex --json
& $cri $acb --cue --index $planIndex -o $cueWav
```

- 默认 ACB 提取面向波形，不能认为一个波形等于一条完整 cue。需要按编排组合音频时使用 `--cue`；它解析并去重可静态展开的 cue 路径，selector 名和值区分不同计划。
- cue 模式 `--index` 是列表中的计划索引，不是 authored cue ID、AWB wave ID 或默认波形列表索引。不要跨模式复用索引。
- `--cue-loop-count N` 控制 authored 无限音频块的额外循环次数，默认 `0`；不是把整条 cue 循环 N 次。`--cue-block-loop-count P=N` 按块位置覆盖，需同时选择 `--index`。
- `--cue-stop-at-loop` 在首个渲染的无限块后停止推进；`--cue-include-empty-holds` 包含默认省略的无波形无限等待。`--raw` 与 `--cue` 互斥。
- 对 ACB AAC 波形可传 `--aac-keycode`。外部 AWB 应与对应 ACB 保持可解析的配套关系；缺失外部波形不能用空音频补齐。
- CLI 能创建/修改 AWB，但不提供 ACB 的通用构建或 mutation。替换 AWB 后仍需验证 ACB 内的 ID、偏移、大小、哈希及外部引用关系。
- AWB 修改：`--replace INDEX=FILE`、`--remove INDEX`、`--move FROM=TO` 按列表索引；`--add FILE=WAVE_ID` 可指定新 wave ID；不支持 `--rename`。

## 其他创建模式

统一形式：`--build -f TYPE INPUT -o OUTPUT`。下列能力按固定版本源码核对；未逐格式实测。

| TYPE | INPUT / 可用配置 |
| --- | --- |
| `afs` | 目录或 `.als` 列表；`--alignment` |
| `awb` | 目录；`--alignment`、`--header-version 0..255`、`--subkey`；alignment 上限 `65535` |
| `acx` | 目录或 `.fls` 列表；`--alignment`，默认 `4` |
| `csb` | 已准备好的 CSB 构建输入；`--encoding`；不把任意音频目录当作完整 cue 表重建输入 |
| `cvm` | 目录或 `.cvs` 构建脚本；可用 `--key` |
| `usm` | 准备好的视频；可重复 `--audio` 加 ADX/HCA、`--alpha`、`--encoding`、`--key`；显式 `--audio-channel 0..255` 时每个 audio 都要一个 channel |
| `sfd` | 准备好的视频，最多一个 `--audio` ADX；`--profile sofdec/sofdec2-v23249/sofdec2-v23310`、`--header-version` |

目录构建 AWB 等时不能假定数字文件名会自动恢复原 wave ID。需保留原 ID 的替换任务优先对已加载容器按索引替换。AFS/AAX/AIX/AWB/CPK/CSB/CVM/ACX 提供不同程度的 mutation，目标语义不同；不要把 CPK 索引规则之外的新增、重命名等操作泛化到所有容器。

```powershell
& $cri --build -f awb $audioDir -o $outputAwb --alignment 32 --header-version 2 --subkey 0
& $cri --build -f usm $videoFile --audio $adxFile --audio $hcaFile -o $outputUsm
& $cri --build -f sfd $videoFile --audio $adxFile -o $outputSfd
```

## 密钥恢复

```powershell
& $cri --recover-key -f hca $sampleHca --json
& $cri --recover-key -f hca $sampleHcaA $sampleHcaB --json
& $cri --recover-key -f usm $sampleUsm --json
& $cri --recover-key -f adx $sampleAdx --json
```

- 恢复域：`hca/usm/adx/ahx/awb/acb`；`awb/acb` 指 CRI AAC keycode 恢复，不是全部音频格式的通用恢复入口。
- 可接受多个输入或目录；默认假定共享基础密钥，`--independent` 改为独立恢复。仅在确有需要且任务授权范围内使用，不作为每次提取的默认步骤。
- 此模式不能附加 `--key/--subkey/--cipher-type/--index/-o/-m/--list/--raw/--encode/--build/--encrypt/--decrypt` 等操作参数。
- 输出为候选与评分，不自动应用到输入；退出 `0` 不等于候选已验证。选择候选后，用独立样本解码检查，再记录是否确证；不要无界枚举重试。
- HCA type 56 恢复不能确定原调用者 keycode 的高 8 位；不能把等效解码 key 声称为 EXE 中的原始 64 位值。

## 实测与失败处理

已用临时合成资源实测：嵌套目录 CPK 创建、JSON 元数据/列表、按索引提取/替换/新增/删除/重命名、输出占位符、CRILAYLA 请求及 UTF 表混淆后提取；48 kHz 单声道 WAV→HCA→WAV、HCA type 56 编码/解密后解码一致性；ADX 编码、AHX 强制解析/解码。CPK 提取后的替换内容与未修改资源做了内容或哈希核对。未据此验证任一游戏的运行兼容性；ACB cue、其他容器构建、密钥恢复未在本次实测。

| 诊断 | AI 助手下一步 |
| --- | --- |
| `unknown option` | 比对本地 `--help`；不要套用旧 Python API、GARbro 或其他版本语法 |
| `only one input path is supported` | 普通操作改成逐文件调用，检查参数是否因空格拆开 |
| `CPK ... target must be an entry index` | 重新列出原始归档，按完整路径取零基索引 |
| 输出位置像目录但实际生成一个文件 | 检查最终选中条目数量；单条目 `-o` 为文件路径 |
| `could not detect supported format` | 核对文件头与已知格式；只有证据明确时用 `-f` |
| JSON 解析失败 | 检查退出码与 stderr、JSON 选项互斥；不要解析混入日志的合并流 |
| 写出成功但游戏读取失败 | 对照原始归档 ID/布局/编码/压缩/加密与音频头参数；保留输出供诊断，不报告为已安装可用 |

维护依据：本地 `--version/--help`、对应版本的 [CLI 参数解析](https://github.com/Youjose/CriCodecs/blob/970f3feaf49e/CriCodecs/src/cli/cli_parse.cpp)、[创建与 mutation 实现](https://github.com/Youjose/CriCodecs/blob/970f3feaf49e/CriCodecs/src/cli/cli_maker.cpp)、[列表与提取实现](https://github.com/Youjose/CriCodecs/blob/970f3feaf49e/CriCodecs/src/cli/cli_export.cpp)。接口冲突时以随附二进制的实测行为为准。
