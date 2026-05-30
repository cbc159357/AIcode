# comic-share 术语表

## 工作流相关

| 术语 | 定义 |
|------|------|
| **API Format JSON** | ComfyUI 通过「Export (API)」导出的格式，只含 `{ nodeId: { class_type, inputs, _meta } }`，无 groups、坐标、links 等画布元数据。RunningHub `getJsonApiFormat` 接口返回此格式。 |
| **完整工作流 JSON** | ComfyUI 通过「Save」或「Export」导出的完整格式，包含 `nodes`（带 pos/size）、`links`、`groups`（带 bounding box）、`extra` 等画布元数据。 |
| **rawNodes** | 本地存储的工作流 API Format 节点字典（即 API Format JSON 的顶层对象）。 |
| **analyzedParams** | 后端从 rawNodes 提取的可调参数平铺列表，按 priority 排序（high→medium→low）。每条含 `nodeId`, `fieldName`, `label`, `type`, `currentValue`, `priority`, `constraints`。 |
| **paramGroups** | 后端从 rawNodes 用 class_type 启发式推断的功能分组列表，每条含 `groupId`, `title`, `defaultCollapsed`, `nodeIds[]`。与 `analyzedParams` 互补，通过 `nodeId` 关联。 |
| **imageInputs** | 工作流中 `LoadImage` 节点的语义标注列表，每条含 `nodeId`, `role`, `label`, `required`。独立于 `paramGroups`，在 WorkflowCard 顶部单独渲染。 |

## 参数分组（groupId 枚举）

| groupId | title | defaultCollapsed | 说明 |
|---------|-------|-----------------|------|
| `prompt` | 提示词 | false | 文本输入类节点 |
| `sampling` | 采样控制 | false | 采样器、种子、步数等 |
| `resolution` | 分辨率 | false | 宽高相关节点 |
| `llm` | AI 模型调用 | true | LLM API 调用节点（model/temperature/max_tokens 等配置） |
| `model` | 模型配置 | true | 模型加载器节点（用户极少修改） |
| `output` | 输出设置 | true | 保存/预览节点 |
| `other` | 其他参数 | false | 不属于以上任何组的剩余节点 |

## 语义角色（imageInputs.role 枚举）

| role | 说明 |
|------|------|
| `reference` | 主参考图（必填） |
| `face` | 脸部一致性参考 |
| `style` | 风格参考 |
| `pose` | 骨骼/姿势参考 |
| `mask` | 遮罩图 |
| `background` | 背景图 |
| `internal` | 内部节点（对用户隐藏） |
