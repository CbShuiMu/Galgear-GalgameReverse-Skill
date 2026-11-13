# UnityFS 图像与事件图抽样

| 工具与来源 | 读取或解包 | 封包或回写 | 验证范围 |
| --- | --- | --- | --- |
| 外部 [UnityPy][upstream] 1.25.4 | 读取 UnityFS 节点、Texture2D 与 Sprite，使用 Pillow 输出 PNG | 本流程为只读 | 真实 Addressables 事件图样本 |

先按 Addressables 路径识别事件图和配套资源，随后以源包、序列化文件及 path ID 标识对象。保留原始 bundle、原样节点及外部纹理流，并将序列化对象和导出的 PNG 分开保存。Texture2D 与 Sprite 即使名称相同也可能表示同图的不同裁剪或范围。已匹配的 Sprite 由读取器按图集关系渲染。[UnityPy 纹理与 Sprite 接口][upstream]

抽样时从每个目标包读取代表对象，记录尺寸、透明通道、原样对象与 PNG 的哈希。按目录或名字分组的变体应保留全部被抽中的来源。实际遮罩、叠层、运行时切换及独立 CG 数须结合游戏脚本进一步验证。

[upstream]: https://github.com/K0lb3/UnityPy

<!-- EXPERIENCE:040832d2a0c3fc65378c8198c8531a7c4d50076eb312be200eb2b3dadd7e2cbf:START -->
## 按 UnityFS 节点及 path ID 保留事件图像与变体

- 引擎版本：UnityFS / Addressables textures
- 方言/条件：Windows，匹配格式的真实样本
- 阶段：extract
- 验证等级：real_sample
- 经验 ID：`040832d2a0c3fc65378c8198c8531a7c4d50076eb312be200eb2b3dadd7e2cbf`

本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。

### 适用前提

- 源包与原样成员清单可核对，使用独立输出目录。

### 已验证步骤

- 验证源包和节点哈希，按对象身份保留原始纹理或 Sprite 并独立导出 PNG。

### 限制与失效条件

- 限匹配的对象与外部流，合成与运行时展示另验。

原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。
<!-- EXPERIENCE:040832d2a0c3fc65378c8198c8531a7c4d50076eb312be200eb2b3dadd7e2cbf:END -->
