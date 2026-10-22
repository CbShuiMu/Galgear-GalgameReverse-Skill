# TyranoScript：网页资源与 KS 场景

TyranoScript 的核心是网页文件和脚本。桌面外壳、移动平台封装与自定义资源保护是另外的层级，没有所有版本共用的 Tyrano 专用归档。

## 解包与封包工具

| 工具与来源 | 解包或读取用途 | 封包或重建用途 | 适用范围与限制 |
| --- | --- | --- | --- |
| 文件系统复制与清单核对，无新增工具依赖 | 对已展开的 `index.html`、`tyrano/`、`data/` 目录建立原样资源根目录 | 在工作副本保留完整路径合并替换资源 | 散文件无需先封成归档；复制后核对路径、数量及哈希，不运行项目 JavaScript |
| [GARbro CLI](../commands/garbro.md)，随附 | 只有实际外层为其支持的 ZIP 等归档时才使用 | 实际外层为可写格式时按该格式创建 | 不是 Tyrano 专用读取器，也不提供通用 ASAR、桌面外壳或项目保护重建 |
| [官方 `@electron/asar` CLI][asar]，外部 MIT 工具 | 外层确为 Electron `app.asar` 时列出并提取 | 创建 ASAR，按实际需要保留 unpacked 资源布局 | 本技能未随附；ASAR 是桌面外壳格式，识别 Tyrano 并不证明一定有 ASAR。Node 版本与运行依赖按所选工具版本核对 |
| [TyranoScript 源码][upstream]及[官方教程][tutorial]，外部参考 | 核对 KS 语法、目录引用及版本配置 | 工作副本可按原结构编辑；正式导出由实际发布环境处理 | 不把源码文档视为已安装 CLI；本任务不启动外壳或重新组织游戏发布构建 |

## 格式特征与编码方式

| 层级 | 通用识别特征 | 编码或变换方式与判定依据 |
| --- | --- | --- |
| 网页项目结构 | 官方结构含 `index.html`、`tyrano/`，以及 `data/scenario`、`data/system`、图像和音频目录 | 目录及相对 URL 是资源引用的一部分；保留大小写、百分号转义和文件后缀，不扁平化成员 |
| HTML / KS / 配置文字 | 所引官方模板声明 `charset=utf-8`；KS 常在 `data/scenario/*.ks`，配置在 `data/system/Config.tjs` | 以官方模板的 UTF-8 文本为基线，并核对实际 HTML charset、响应头及加载实现。异常代码页或自定义 loader 不是引擎通则；`.tjs` 后缀本身不证明它是 KiriKiri 可执行脚本 |
| 场景语法 | [parser][parser]读取普通文字、`[tag ...]`、`@tag`、`*label`、`;` 注释及 `#角色` 等 | 语法先于清理文本；保留行号、标签、参数与实际引用。KS 与 KAG 外观相近，不保证可以用同一解析器 |
| 压缩、加密与外壳 | 核心项目资源通常是散文件；外层可由发布环境决定 | 不存在本页可给出的统一压缩或密钥。实际是 ASAR 时，它按官方说明将文件连接并使用结构化头，不做通用成员压缩；ZIP、外壳保护或插件变换另查对应实现 |
| 图像、音频与视频 | `data/` 中分目录存放媒体，具体引用由标签和配置给出 | 按真实文件头、浏览器/外壳版本和插件判断支持格式；文字 UTF-8 不影响媒体编码，不能因目录叫 `sound` 就假定固定 codec |

## 注意事项

- 先区分网页散文件、归档和桌面外壳。外壳完整性校验、签名、`app.asar.unpacked` 与本地模块会限制重新封装；没有证据时不承诺只替换一个 ASAR 即可加载。
- `#角色` 可能引用角色标识和表情，宏与插件可改写消息及播放行为。需要对白与语音关联时读实际版本标签实现与调用点，不根据相邻文件名或文本行号猜配。
- 提取阶段不执行 `index.html` 或项目脚本；原样资源根目录与文本工作副本分开。修改后先比较路径和字节，再按用户需要安排浏览器或外壳验证。

## 来源、版本与验证边界

核心依据官方 TyranoScript `c8dbfd492afd3d79b0954fcf4477236f5c6c4830` 的模板、parser 和加载实现，以及官方目录教程；ASAR 参考 `electron/asar` 的 `610035abdb6c25b7c26ead1c9853c2b9de3ddb69`。本页为官方资料与源码阅读等级，没有真实游戏或运行验证。不同代际、第三方桌面外壳、自定义 loader、保护或媒体插件与上述依据不符时，重新检查具体实现；单款游戏的参数与密钥留在用户本地。

[upstream]: https://github.com/ShikemokuMK/tyranoscript/tree/c8dbfd492afd3d79b0954fcf4477236f5c6c4830
[parser]: https://github.com/ShikemokuMK/tyranoscript/blob/c8dbfd492afd3d79b0954fcf4477236f5c6c4830/tyrano/plugins/kag/kag.parser.js
[tutorial]: https://tyrano.jp/usage/tutorial/moji
[asar]: https://github.com/electron/asar/tree/610035abdb6c25b7c26ead1c9853c2b9de3ddb69
