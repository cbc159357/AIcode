# comic-share 布局重构方案

> 创建日期: 2026-05-28
> 状态: 设计阶段（不修改代码）
> 前置: Phase 1-6 全部完成，功能代码齐备

---

## 一、重构目标

将当前 **三栏固定布局**（LeftPanel + 中间工作台 + RightPanel）重构为：

1. **左侧边栏** — 三种模式切换（工作台 / 工作流 / 设置）
2. **中间主区域** — 占满剩余空间，是核心操作区
3. **右侧预览** — 改为 **默认收起的右抽屉**，按需展开

---

## 二、当前布局分析

### 现状结构

```
┌─────────────────────────────────────────────────────────────────┐
│ TopBar（顶栏：服务状态灯）                                        │
├──────────┬──────────────────────────────────┬───────────────────┤
│ LeftPanel│        中间工作台                 │    RightPanel     │
│ w-80     │   分镜板 Tab / LLM 输出 Tab       │    w-96           │
│          │                                  │                   │
│ · 故事输入│                                  │ · 视频预览区       │
│ · 流程控制│                                  │ · 进度条           │
│ · 配置Tab │                                  │ · 运行日志         │
│ (LLM/风格│                                  │                   │
│  /生图/  │                                  │                   │
│  TTS/音频)│                                  │                   │
└──────────┴──────────────────────────────────┴───────────────────┘
```

### 问题

- **LeftPanel 职责过重** — 故事输入 + 4步流程 + 5个配置Tab 全挤在 w-80 面板
- **RightPanel 永久占位** — 视频预览区大部分时间空白，浪费 w-96 水平空间
- **无模式区分** — 工作流管理、设置等功能无入口，全部堆砌在一个面板
- **中间区域被压缩** — 左右各固定宽度，分镜板可用空间不足

---

## 三、新布局设计

### 3.1 整体结构

```
┌─────────────────────────────────────────────────────────────┬──────┐
│ TopBar（顶栏：服务状态灯 + 预览按钮）                         │      │
├────┬────────────────────────────────────────────────────────┤      │
│图标│         中间主区域（flex-1，占满）                       │ 右抽屉│
│侧栏│                                                       │(默认 │
│w-14│  根据左侧模式切换内容:                                  │ 收起) │
│    │  · 工作台模式 → 故事输入+流程+分镜板+LLM                 │      │
│    │  · 工作流模式 → 工作流列表+编辑                          │ 展开时│
│    │  · 设置模式   → 全局配置                                │ w-96 │
│    │                                                       │      │
│ 🏠 │                                                       │ · 预览│
│ 📋 │                                                       │ · 进度│
│ ⚙️ │                                                       │ · 日志│
└────┴────────────────────────────────────────────────────────┴──────┘
```

### 3.2 左侧图标侧栏（IconSidebar）

**宽度**: w-14（56px），紧凑图标式

**三种模式**:

| 图标 | 模式 | 说明 |
|------|------|------|
| lucide:layout-dashboard | 工作台 | 创作主流程（默认激活） |
| lucide:git-branch | 工作流 | ComfyUI/RunningHub 工作流管理 |
| lucide:settings | 设置 | LLM/生图/TTS/音频全局配置 |

**交互**: 点击图标切换模式 → 中间主区域内容随之切换

### 3.3 中间主区域（根据模式动态渲染）

#### 模式 A: 工作台（默认）

当前 LeftPanel 的「故事输入 + 流程控制」移到主区域顶部或左侧子面板：

```
┌─────────────────────────────────────────────┐
│ 顶部操作栏                                    │
│ [故事文本输入区] [步骤1] [步骤2] [步骤3] [步骤4] │
├──────────────────┬──────────────────────────┤
│  分镜板           │  LLM 输出（可折叠）        │
│  (ShotGrid)      │  (LLMOutput)             │
│                  │                          │
│                  │                          │
└──────────────────┴──────────────────────────┘
```

**功能来源**: 
- 故事输入 — 原 LeftPanel 的 `<a-textarea>`
- 流程控制 — 原 LeftPanel 的 4 个 `<a-button>`（横向排列更省空间）
- 分镜板 — 原 WorkStation.vue 的 ShotGrid Tab
- LLM 输出 — 原 WorkStation.vue 的 LLMOutput Tab

#### 模式 B: 工作流

工作流管理面板（ComfyUI 工作流 + RunningHub 工作流列表）：

```
┌─────────────────────────────────────────────┐
│ 工作流列表                                    │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐         │
│ │ T2I     │ │ I2V     │ │ Edit    │         │
│ │ nunchaku│ │ Wan2.1  │ │ Qwen   │         │
│ └─────────┘ └─────────┘ └─────────┘         │
│                                              │
│ [上传工作流] [从 RunningHub 拉取]               │
├──────────────────────────────────────────────┤
│ 工作流详情 / 参数编辑                           │
│ （选中卡片后展开）                              │
└──────────────────────────────────────────────┘
```

**功能来源**: 
- 后端已有 `routers/comfyui.py`（list_workflows, get_workflow）
- 前端已有 `services/comfyui.ts`
- 需新增: `views/WorkflowManager.vue` 或 `components/workflow/` 目录

#### 模式 C: 设置

将原 LeftPanel 的 5 个配置 Tab 全部展开为完整设置页面：

```
┌─────────────────────────────────────────────┐
│ 设置                                         │
│                                              │
│ ┌── LLM 配置 ──────────────────────────────┐ │
│ │ Provider / Model / API Key / Temp / Max  │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ ┌── 风格配置 ──────────────────────────────┐ │
│ │ 画风预设 / 时代背景                       │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ ┌── 生图配置 ──────────────────────────────┐ │
│ │ 引擎选择 / 模型 / 图片尺寸               │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ ┌── TTS 配置 ─────────────────────────────┐ │
│ │ 服务地址 / 音色                          │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ ┌── 音频配置 ─────────────────────────────┐ │
│ │ BGM 开关 / 字幕开关                      │ │
│ └──────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

**功能来源**: 
- 原 LeftPanel 的 5 个 Config 组件（LLMConfig/StyleConfig/ImageConfig/TTSConfig/AudioConfig）
- 原 Settings.vue（占位页）可合并或删除

### 3.4 右侧预览抽屉（PreviewDrawer）

**默认状态**: 收起（不占水平空间）

**触发方式**: 
- TopBar 右侧「预览」按钮点击切换
- 步骤4完成后自动展开
- 快捷键（如 `Ctrl+P`）

**展开宽度**: w-96（384px），从右侧滑入

**内容**（与当前 RightPanel 一致）:
- 视频预览区（aspect-video）
- 进度条（progressLabel + progressPercent）
- 运行日志（logs 列表 + 清除按钮）

**实现方式**: Arco Design `<a-drawer>` 组件，`placement="right"`, `width="384"`

---

## 四、组件映射（旧 → 新）

| 旧组件 | 新位置 | 说明 |
|--------|--------|------|
| `LeftPanel.vue` 故事输入区 | 工作台模式顶部 | 从侧栏移到主区域 |
| `LeftPanel.vue` 流程控制区 | 工作台模式顶部操作栏 | 4按钮横向排列 |
| `LeftPanel.vue` 配置面板 | 设置模式主区域 | 5个Tab展开为卡片列表 |
| `RightPanel.vue` | `PreviewDrawer.vue` | 改为 a-drawer，默认收起 |
| `WorkStation.vue` Tab 区 | 工作台模式主区域 | 分镜板+LLM输出 |
| `Settings.vue` | 删除或合并 | 功能归入设置模式 |
| `TopBar.vue` | 保留 + 新增预览按钮 | 右侧加抽屉触发按钮 |

---

## 五、新增/修改文件清单

### 新增

| 文件 | 说明 |
|------|------|
| `components/layout/IconSidebar.vue` | 图标侧栏（w-14），3个模式图标 |
| `components/layout/PreviewDrawer.vue` | 右侧预览抽屉（a-drawer） |
| `components/workspace/WorkspaceView.vue` | 工作台模式内容（故事输入+流程+分镜） |
| `components/workflow/WorkflowManager.vue` | 工作流管理模式内容 |
| `components/settings/SettingsView.vue` | 设置模式内容（5个配置卡片） |

### 修改

| 文件 | 改动 |
|------|------|
| `WorkStation.vue` | 三栏 → 双栏（IconSidebar + 主区域），条件渲染3种模式，右抽屉 |
| `TopBar.vue` | 右侧新增预览按钮（toggle drawer） |
| `LeftPanel.vue` | 删除或保留为空壳（功能分散到各模式组件） |
| `RightPanel.vue` | 删除（功能迁入 PreviewDrawer） |
| `stores/app.ts` | 新增 `sidebarMode` 状态 + `previewDrawerOpen` 状态 |

### 可复用（无需修改）

| 文件 | 说明 |
|------|------|
| 5 个 Config 组件 | 直接在 SettingsView 中引用 |
| ShotGrid / ShotCard | 直接在 WorkspaceView 中引用 |
| LLMOutput | 直接在 WorkspaceView 中引用 |
| 全部 services/ | 不涉及布局 |
| 全部 composables/ | 不涉及布局 |
| 全部 stores/ (config/project) | 不涉及布局 |
| 全部 backend/ | 不涉及前端布局 |

---

## 六、状态管理变更

### `stores/app.ts` 新增字段

```ts
// 侧栏模式
type SidebarMode = 'workspace' | 'workflow' | 'settings'
sidebarMode: SidebarMode  // 默认 'workspace'

// 预览抽屉
previewDrawerOpen: boolean  // 默认 false
```

### WorkStation.vue 主逻辑

```vue
<!-- 伪代码，不做实际实现 -->
<IconSidebar v-model:mode="appStore.sidebarMode" />

<main class="flex-1">
  <WorkspaceView v-if="appStore.sidebarMode === 'workspace'" />
  <WorkflowManager v-else-if="appStore.sidebarMode === 'workflow'" />
  <SettingsView v-else />
</main>

<PreviewDrawer v-model:open="appStore.previewDrawerOpen" />
```

---

## 七、交互细节

### 预览抽屉

| 行为 | 说明 |
|------|------|
| 默认状态 | 收起，不可见 |
| 打开方式 | TopBar 预览按钮 / 步骤4完成自动 / 快捷键 |
| 关闭方式 | 抽屉关闭按钮 / 遮罩点击 / ESC / 再次点击预览按钮 |
| 遮罩 | 半透明遮罩（可选，也可无遮罩 push 模式） |
| 动画 | 从右侧滑入，300ms ease |

### 侧栏模式切换

| 行为 | 说明 |
|------|------|
| 默认模式 | 工作台 |
| 切换动画 | 无（即时切换，v-if） |
| 状态保持 | 切换模式不丢失表单数据（config store 已持久化） |
| 视觉反馈 | 当前模式图标高亮（蓝色背景/边框） |

---

## 八、收益

| 维度 | 改进 |
|------|------|
| **水平空间** | 右侧默认收起，节省 384px；左侧从 w-80 缩到 w-14，净增 ~400px 给主区域 |
| **职责清晰** | 工作台专注创作、工作流专注管理、设置专注配置 |
| **配置体验** | 5个配置从挤压的 Tab 展开为完整卡片，表单更易操作 |
| **可扩展** | 后续新增模式只需加图标+视图组件 |
| **代码复用** | Config/Shot/LLM 组件零修改，只改容器 |

---

## 九、实施步骤（建议）

1. 新建 `IconSidebar.vue` + `PreviewDrawer.vue`
2. 新建 `WorkspaceView.vue`（从 LeftPanel + WorkStation 提取）
3. 新建 `SettingsView.vue`（引用 5 个 Config 组件）
4. 新建 `WorkflowManager.vue`（骨架 + 调用已有 comfyui service）
5. 重写 `WorkStation.vue`（IconSidebar + 模式切换 + PreviewDrawer）
6. 更新 `stores/app.ts`（sidebarMode + previewDrawerOpen）
7. 更新 `TopBar.vue`（预览按钮）
8. 删除 `LeftPanel.vue` + `RightPanel.vue`（功能已分散）
9. `vue-tsc --noEmit` + `vite build` 验证
