# GARbro CLI 命令与选项


可执行文件：相对于 GalExtract 技能目录的 `tools/GARbro-cli/GARbro.Console.exe`。其 DLL、配置文件、语言资源目录和 `GameData/` 应保持原有相对位置。包含空格的路径应使用双引号。命令与开关区分大小写；格式标签和 `-O` 选项名称不区分大小写。下方示例中的 `.\GARbro.Console.exe` 假定当前目录为该运行目录；在其他目录调用时，应使用已解析的可执行文件路径。

## 命令

| 命令 | 用法 | 用途 |
| --- | --- | --- |
| `h` | `GARbro.Console.exe h` | 显示帮助。别名：`-h`、`--help`、`/?`、`-?`。无参数运行也会显示帮助 |
| `f` | `GARbro.Console.exe f [-q]` | 列出可识别的归档格式标签与说明 |
| `f --writable` | `GARbro.Console.exe f --writable [-q]` | 列出支持创建的格式、扩展名及写入器是否支持子目录。`-w` 是 `--writable` 的别名 |
| `options` | `GARbro.Console.exe options <Tag> [-q]` | 列出格式的创建选项、类型、当前默认值和枚举值。复杂类型会标记为无法通过 CLI 赋值 |
| `i` | `GARbro.Console.exe i [options] <file>` | 识别归档或单个图片、音频文件 |
| `l` | `GARbro.Console.exe l [options] <file>` | 列出条目名称、偏移和大小 |
| `x` | `GARbro.Console.exe x [options] <file>` | 提取归档，或对单个图片、音频文件执行转换流程 |
| `c` / `pack` | `GARbro.Console.exe c -t <Tag> -o <archive> [options] <input-directory>` | 将目录中的文件封包为指定格式的归档 |

## 创建选项（`c` / `pack`）

输入目录必须是最后一个参数。默认仅包含该目录直接下属的文件。不保存空目录。

| 选项 | 用途 |
| --- | --- |
| `-t <Tag>` / `--type <Tag>` | **必需。** 指定完整格式标签，例如 `XP3`、`ZIP` 或 `ARC/Will`。可用标签见 `f --writable`。不会根据输出扩展名推断格式 |
| `-o <file>` / `--output <file>` | **必需。** 输出归档路径。相对路径以启动 CLI 的目录为基准解析。自动创建父目录 |
| `-R` / `--recursive` | 递归包含子目录。格式写入器不支持子目录时，匹配到嵌套文件会报错 |
| `-f <regex>` / `--filter <regex>` | 只包含匹配文件。匹配相对于输入目录、使用 `/` 分隔符的路径。默认区分大小写 |
| `-O <Name=Value>` / `--option <Name=Value>` | 设置格式特定选项，可重复。同一选项重复赋值时，以最后一个值为准。参见 `options <Tag>` |
| `-y` / `--overwrite` | 覆盖已有输出归档 |
| `-s` / `--skip` | 输出归档存在时跳过创建，并返回非零退出码 |
| `-r` / `--rename` | 输出已存在时，使用 `name (2).extension`，递增编号直到找到未使用名称 |
| `-q` / `--quiet` | 隐藏横幅、进度和成功消息。错误仍写入 stderr；输出路径仍写入 stdout |
| `-h` / `--help` | 使用 `c --help` 或 `pack --help` 显示帮助 |

布尔值使用 `true` / `false`。整数接受十进制或带 `0x` 前缀的十六进制。枚举接受成员名称。编码接受 `utf-8`、`shift_jis` 等名称。字节数组接受连续十六进制数字，可选 `0x` 前缀。赋值包含空格时，为整个赋值加引号，例如 `-O "BaseArchive=original files\data.ami"`。

## 格式特定创建选项（`-O`）

当前构建提供以下 19 种可写格式。运行 `options <Tag>` 查看本机默认值；GARbro 用户设置可能影响这些值。

| 格式 | 选项与用途 | 子目录 |
| --- | --- | --- |
| `AMI` | `UseBaseArchive`：与基准归档合并，默认 `false`。`BaseArchive`：基准归档路径；相对路径以启动目录为基准解析 | 否 |
| `ARC/Will` | `NameLength`：不含扩展名的文件名字段长度；仅接受 `8` 或 `12`，默认 `8` | 否 |
| `ARC/WillV2` | 无格式特定选项 | 否 |
| `DAT/EGO/1` | 无格式特定选项 | 是 |
| `INT` | 无格式特定创建选项；创建未加密归档 | 否 |
| `MAJIRO` | 无格式特定选项 | 否 |
| `NPA` | `CompressContents`：压缩文件内容，默认 `false`。`Key1`、`Key2`：引擎索引处理使用的整数密钥。`Scheme` 是复杂加密方案对象，只使用引擎默认值，不支持通过 CLI 赋值 | 是 |
| `NPA-SG` | `FileNameEncoding`：文件名编码，默认 `shift_jis` | 是 |
| `NPK` | `Key`：AES 密钥字节数组，以 32、48 或 64 个十六进制数字提供。没有可用默认密钥时必须指定 | 是 |
| `NSA` | `CompressionType`：`None`（默认）或 `LZSS`。LZSS 仅用于 `.bmp` 文件，其他文件原样存储。写入器不支持 SPB、NBZ 或密码保护 | 是 |
| `PAK/HyPack` | 无格式特定选项 | 否 |
| `PD` | `ScrambleContents`：扰乱文件内容，默认 `false` | 否 |
| `RPA` | `Key`：对索引偏移和大小进行 XOR 的无符号 32 位整数；这不属于安全加密 | 是 |
| `SAR` | 无格式特定选项 | 是 |
| `XFL` | 无格式特定选项。当前写入器仅保存基本文件名，因此拒绝嵌套输入 | 否 |
| `XP3` | `Version`：`1` 或 `2`，默认 `2`。`CompressIndex`：压缩索引，默认 `true`。`CompressContents`：压缩符合条件的资源，默认 `false`。`RetainDirs`：保留目录路径，CLI 默认 `true`。`Scheme` 是复杂加密方案对象，只使用引擎默认值，不支持通过 CLI 赋值 | 是；要求 `RetainDirs=true` |
| `YKC` | 无格式特定选项 | 是 |
| `YPF` | `Key`：文件名 XOR 密钥，范围 `0` 到 `255`。引擎默认值 `4294967295` 表示未指定，创建前必须替换。`Version`：整数格式版本，默认 `290`。当前写入器仅支持旧版索引布局；CLI 接受 `1` 到 `472`，但不含 `222`。版本必须匹配目标游戏 | 是 |
| `ZIP` | `CompressionLevel`：`Optimal`（默认）、`Fastest` 或 `NoCompression`。`FileNameEncoding`：文件名编码，默认 `shift_jis`。写入器不支持密码保护 | 是 |

部分引擎要求特定文件名、字符编码、版本或脚本结构。例如，AMI 仅接受以十六进制资源 ID 命名的图片或 `.scr` 文件，且 ID 必须唯一。ARC/Will 的扩展名最多 3 字节，并会规范化文件名大小写。许多写入器使用 CP932，会拒绝无法编码的文件名。CLI 复用现有写入器；支持创建并不保证兼容目标游戏的每个版本。

单个输入文件大小上限为 `uint.MaxValue` 字节。具体格式还可能限制归档总大小、名称长度和文件数量。SAR 和 NSA 最多支持 32767 个文件。递归封包拒绝目录链接，文件符号链接也不能作为资源输入。

## 识别、列表与提取选项（`i` / `l` / `x`）

输入文件必须是最后一个参数。以下短选项保留原始 CLI 行为。

| 选项 | 用途 |
| --- | --- |
| `-o <directory>` | `x` 的输出目录，默认为当前目录 |
| `-f <regex>` | 按条目名称过滤资源 |
| `-if <format>` | 对 `x`，将图片转换为指定格式，如 `png`、`jpg` 或 `bmp`。`jpg` 映射为 `JPEG` |
| `-ca` | 对 `x`，保留常见 `wav`、`mp3` 和 `ogg` 音频格式；其他可解码音频写为 WAV |
| `-na` | 排除音频条目 |
| `-ni` | 排除图片条目 |
| `-ns` | 排除脚本条目 |
| `-aio` | 图片转换时应用图像偏移并调整输出画布 |
| `-ocu` | 需要 `-if`。保留常见 JPEG、PNG、BMP 和 TGA 格式；其他图片转换为 PNG |
| `-y` / `--overwrite` | 覆盖已有提取输出文件 |
| `-s` / `--skip` | 跳过已有提取输出文件 |
| `-r` / `--rename` | 将冲突输出文件重命名为 `name (2).extension`，按需递增编号 |
| `-q` / `--quiet` | 隐藏横幅与常规进度；错误仍写入 stderr |

未指定已有文件处理策略时，stdin 已重定向的非交互调用默认覆盖。交互终端会询问覆盖、跳过或重命名。批处理应显式指定 `-y`、`-s` 或 `-r`。提供多个策略时，以最后一个为准。

## 示例

```powershell
# 查询可写格式与 XP3 选项
.\GARbro.Console.exe f --writable
.\GARbro.Console.exe options XP3

# 递归创建 XP3，压缩符合条件的文件内容
.\GARbro.Console.exe c -t XP3 -o patch.xp3 -R -O CompressContents=true -y .\resources

# 仅包含 scripts 子目录下的 TJS 文件
.\GARbro.Console.exe pack -t XP3 -o scripts.xp3 -R -f '^scripts/.*\.tjs$' .\resources

# 创建使用 UTF-8 文件名的 ZIP
.\GARbro.Console.exe c -t ZIP -o data.zip -R -O FileNameEncoding=utf-8 .\resources

# 创建 YPF；密钥和版本须匹配目标游戏
.\GARbro.Console.exe c -t YPF -o patch.ypf -R -O Key=0xff -O Version=290 .\resources

# 识别、列出并提取
.\GARbro.Console.exe i patch.xp3
.\GARbro.Console.exe l -f '\.tjs$' patch.xp3
.\GARbro.Console.exe x -y -q -o .\unpacked patch.xp3
```

## 输出与退出码

| 项目 | 含义 |
| --- | --- |
| stdout | 帮助、格式列表、选项列表、识别结果及条目列表。创建成功后输出最终归档的绝对路径 |
| stderr | 横幅、进度、警告和错误。`-q` 隐藏常规消息但保留错误 |
| `0` | 成功，包括帮助和查询 |
| `1` | 参数无效、格式或选项不支持、没有匹配文件、创建或处理失败等错误 |

创建时先在输出目录写入临时文件，成功后替换目标。失败时清理临时文件并保留已有目标。如果输出归档位于输入目录内，该目标本身会从输入列表中排除。

